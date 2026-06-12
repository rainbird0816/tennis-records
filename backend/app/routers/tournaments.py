"""대회 라우터 (§7).

GET /tournaments/{tour}/{tourney_id}   대회 메타 + 라운드별 경기(브래킷)
GET /series/{slug}/champions?tour=     역대 우승자
GET /series/{slug}/records?tour=       대회 기록(개관)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..db import query, query_one

router = APIRouter()


def _age_str(dob: str | None, on_date: str | None) -> tuple[int | None, str | None]:
    """dob·기준일(YYYYMMDD) → (총 일수, "NN세 MM개월") 근사. 대회 시작일 기준."""
    if not dob or not on_date or len(dob) < 8 or len(on_date) < 8:
        return None, None
    try:
        by, bm, bd = int(dob[:4]), int(dob[4:6]), int(dob[6:8])
        oy, om, od = int(on_date[:4]), int(on_date[4:6]), int(on_date[6:8])
    except ValueError:
        return None, None
    years = oy - by
    months = om - bm
    if od < bd:
        months -= 1
    if months < 0:
        years -= 1
        months += 12
    # 정렬용 근사 일수
    days = (oy * 365 + om * 30 + od) - (by * 365 + bm * 30 + bd)
    return days, f"{years}세 {months}개월"


@router.get("/tournaments/{tour}/{tourney_id}")
def tournament_detail(tour: str, tourney_id: str) -> dict:
    meta = query_one(
        "SELECT * FROM tournaments WHERE tour = ? AND tourney_id = ?",
        (tour, tourney_id),
    )
    if not meta:
        raise HTTPException(404, "tournament not found")
    matches = query(
        """
        SELECT m.match_id, m.round, m.round_order, m.best_of,
               m.winner_id, m.loser_id, m.winner_seed, m.loser_seed,
               m.winner_rank, m.loser_rank, m.score, m.outcome, m.minutes, m.has_stats,
               wp.full_name AS winner_name, lp.full_name AS loser_name,
               wp.ioc AS winner_ioc, lp.ioc AS loser_ioc
        FROM matches m
        LEFT JOIN players wp ON wp.tour = m.tour AND wp.player_id = m.winner_id
        LEFT JOIN players lp ON lp.tour = m.tour AND lp.player_id = m.loser_id
        WHERE m.tour = ? AND m.tourney_id = ?
        ORDER BY m.round_order, m.match_num
        """,
        (tour, tourney_id),
    )
    return {"tournament": meta, "matches": matches}


@router.get("/series/{slug}/champions")
def series_champions(
    slug: str,
    tour: str = Query(..., pattern="^(atp|wta)$"),
) -> dict:
    """시리즈(대회명 슬러그)의 역대 우승자. champions 뷰 사용 (§5)."""
    champs = query(
        """
        SELECT c.season, c.name, c.surface, c.tourney_id,
               c.champion_id, c.runnerup_id, c.score,
               t.start_date, t.tier, t.draw_size,
               wp.full_name AS champion_name, lp.full_name AS runnerup_name
        FROM champions c
        JOIN tournaments t ON t.tour = c.tour AND t.tourney_id = c.tourney_id
        LEFT JOIN players wp ON wp.tour = c.tour AND wp.player_id = c.champion_id
        LEFT JOIN players lp ON lp.tour = c.tour AND lp.player_id = c.runnerup_id
        WHERE c.tour = ? AND c.name = ?
        ORDER BY c.season DESC, t.start_date DESC
        """,
        (tour, slug),
    )
    return {"slug": slug, "tour": tour, "champions": champs}


@router.get("/series/{slug}/records")
def series_records(
    slug: str,
    tour: str = Query(..., pattern="^(atp|wta)$"),
) -> dict:
    """대회 개관: 최다 우승·최다 연속 우승·최장 경기·최고령/최연소 우승 등."""
    # 역대 우승자(시즌 오름차순) — 연속 우승·통산 우승 집계용.
    champs = query(
        """
        SELECT c.season, c.tourney_id, c.surface, c.champion_id, c.runnerup_id,
               c.score, t.start_date,
               wp.full_name AS champion_name, wp.ioc AS champion_ioc, wp.dob AS champion_dob
        FROM champions c
        JOIN tournaments t ON t.tour = c.tour AND t.tourney_id = c.tourney_id
        LEFT JOIN players wp ON wp.tour = c.tour AND wp.player_id = c.champion_id
        WHERE c.tour = ? AND c.name = ?
        ORDER BY c.season ASC, t.start_date ASC
        """,
        (tour, slug),
    )
    if not champs:
        raise HTTPException(404, "series not found")

    # 통산 우승 / 결승 진출 횟수
    title_n: dict[int, int] = {}
    final_n: dict[int, int] = {}
    info: dict[int, dict] = {}
    for c in champs:
        cid = c["champion_id"]
        title_n[cid] = title_n.get(cid, 0) + 1
        final_n[cid] = final_n.get(cid, 0) + 1
        final_n[c["runnerup_id"]] = final_n.get(c["runnerup_id"], 0) + 1
        info[cid] = {"player_id": cid, "name": c["champion_name"], "ioc": c["champion_ioc"]}

    # 준우승자 이름/국기 (결승 진출 랭킹 표기용)
    ru_ids = [c["runnerup_id"] for c in champs if c["runnerup_id"] not in info]
    if ru_ids:
        ph = ",".join("?" * len(ru_ids))
        for r in query(
            f"SELECT player_id, full_name, ioc FROM players WHERE tour=? AND player_id IN ({ph})",
            (tour, *ru_ids),
        ):
            info[r["player_id"]] = {"player_id": r["player_id"], "name": r["full_name"], "ioc": r["ioc"]}

    def leaders(counts: dict[int, int], limit: int = 5) -> list[dict]:
        top = sorted(counts.items(), key=lambda kv: (-kv[1], info.get(kv[0], {}).get("name") or ""))
        return [{**info.get(pid, {"player_id": pid, "name": None, "ioc": None}), "count": n}
                for pid, n in top[:limit]]

    # 최다 연속 우승 (개최 에디션 연속 기준)
    best = {"count": 0, "player_id": None, "seasons": []}
    run_id, run_seasons = None, []
    for c in champs:
        if c["champion_id"] == run_id:
            run_seasons.append(c["season"])
        else:
            run_id, run_seasons = c["champion_id"], [c["season"]]
        if len(run_seasons) > best["count"]:
            best = {"count": len(run_seasons), "player_id": run_id, "seasons": list(run_seasons)}
    most_consecutive = None
    if best["player_id"] is not None and best["count"] >= 2:
        most_consecutive = {**info.get(best["player_id"], {}), "count": best["count"], "seasons": best["seasons"]}

    # 최고령 / 최연소 우승 (대회 시작일 기준 근사)
    aged = []
    for c in champs:
        days, label = _age_str(c["champion_dob"], c["start_date"])
        if days is not None:
            aged.append({**info.get(c["champion_id"], {}), "season": c["season"],
                         "age_days": days, "age_str": label})
    oldest = max(aged, key=lambda a: a["age_days"]) if aged else None
    youngest = min(aged, key=lambda a: a["age_days"]) if aged else None

    # 최장 시간 경기 (분)
    longest = query_one(
        """
        SELECT m.match_id, m.minutes, m.round, m.score, t.season,
               wp.full_name AS winner_name, wp.ioc AS winner_ioc,
               lp.full_name AS loser_name, lp.ioc AS loser_ioc
        FROM matches m
        JOIN tournaments t ON t.tour = m.tour AND t.tourney_id = m.tourney_id
        LEFT JOIN players wp ON wp.tour = m.tour AND wp.player_id = m.winner_id
        LEFT JOIN players lp ON lp.tour = m.tour AND lp.player_id = m.loser_id
        WHERE m.tour = ? AND t.name = ? AND m.minutes IS NOT NULL AND m.minutes > 0
        ORDER BY m.minutes DESC LIMIT 1
        """,
        (tour, slug),
    )

    surfaces = sorted({c["surface"] for c in champs if c["surface"]})
    return {
        "slug": slug,
        "tour": tour,
        "summary": {
            "editions": len(champs),
            "first_season": champs[0]["season"],
            "last_season": champs[-1]["season"],
            "surfaces": surfaces,
        },
        "most_titles": leaders(title_n),
        "most_finals": leaders(final_n),
        "most_consecutive": most_consecutive,
        "oldest_champion": oldest,
        "youngest_champion": youngest,
        "longest_match": longest,
    }
