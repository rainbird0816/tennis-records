"""H2H · 기록 · 검색 · 올림픽 메달 라우터 (§7, §9.4).

GET /olympics/{season}/medals    남·녀 금/은/동
GET /h2h?p1=&p2=&tour=           상대전적
GET /records?tier=&tour=&metric= 기록
GET /search?q=&tour=             선수/대회 검색
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from ..db import query

router = APIRouter()


@router.get("/olympics/{season}/medals")
def olympics_medals(season: int) -> dict:
    medals = query(
        """
        SELECT tour, medal, player_id
        FROM olympic_medals
        WHERE season = ?
        ORDER BY tour, CASE medal WHEN 'gold' THEN 0 WHEN 'silver' THEN 1 ELSE 2 END
        """,
        (season,),
    )
    return {"season": season, "medals": medals}


@router.get("/h2h")
def head_to_head(
    p1: int,
    p2: int,
    tour: str = Query(..., pattern="^(atp|wta)$"),
) -> dict:
    rows = query(
        """
        SELECT m.match_id, m.tourney_id, m.round, m.round_order, m.score,
               t.surface, t.season, t.tier, t.name AS tournament_name,
               m.winner_id, m.loser_id,
               wp.full_name AS winner_name, lp.full_name AS loser_name
        FROM matches m
        JOIN tournaments t ON t.tour = m.tour AND t.tourney_id = m.tourney_id
        LEFT JOIN players wp ON wp.tour = m.tour AND wp.player_id = m.winner_id
        LEFT JOIN players lp ON lp.tour = m.tour AND lp.player_id = m.loser_id
        WHERE m.tour = :tour
          AND ((m.winner_id = :p1 AND m.loser_id = :p2)
            OR (m.winner_id = :p2 AND m.loser_id = :p1))
        ORDER BY t.season DESC, t.start_date DESC
        """,
        {"tour": tour, "p1": p1, "p2": p2},
    )

    names = {
        r["player_id"]: r["full_name"]
        for r in query(
            "SELECT player_id, full_name FROM players "
            "WHERE tour = ? AND player_id IN (?, ?)",
            (tour, p1, p2),
        )
    }

    # 서피스/라운드/tier 분해 (§9.4): 각 차원별 p1 승 수 집계.
    def breakdown(key: str) -> list[dict]:
        agg: dict[str, list[int]] = {}
        for r in rows:
            k = r[key] or "?"
            agg.setdefault(k, [0, 0])
            agg[k][0 if r["winner_id"] == p1 else 1] += 1
        return [
            {key: k, "p1_wins": v[0], "p2_wins": v[1]}
            for k, v in sorted(agg.items())
        ]

    p1_wins = sum(1 for r in rows if r["winner_id"] == p1)
    return {
        "tour": tour,
        "p1": p1, "p2": p2,
        "p1_name": names.get(p1), "p2_name": names.get(p2),
        "summary": {"total": len(rows), "p1_wins": p1_wins, "p2_wins": len(rows) - p1_wins},
        "by_surface": breakdown("surface"),
        "by_tier": breakdown("tier"),
        "by_round": breakdown("round"),
        "matches": rows,
    }


@router.get("/records")
def records(
    tier: str = Query(...),
    tour: str = Query(..., pattern="^(atp|wta)$"),
    metric: str = Query("titles", pattern="^(titles|finals)$"),
) -> dict:
    """tier별 통산 우승(titles) 또는 결승 진출(finals) 횟수 랭킹."""
    if metric == "finals":
        # 우승 + 준우승 = 결승 진출
        rows = query(
            """
            SELECT x.player_id, p.full_name, COUNT(*) AS n FROM (
                SELECT champion_id AS player_id FROM champions WHERE tier = ? AND tour = ?
                UNION ALL
                SELECT runnerup_id AS player_id FROM champions WHERE tier = ? AND tour = ?
            ) x
            LEFT JOIN players p ON p.tour = ? AND p.player_id = x.player_id
            GROUP BY x.player_id ORDER BY n DESC LIMIT 50
            """,
            (tier, tour, tier, tour, tour),
        )
    else:
        rows = query(
            """
            SELECT c.champion_id AS player_id, p.full_name, COUNT(*) AS n
            FROM champions c
            LEFT JOIN players p ON p.tour = c.tour AND p.player_id = c.champion_id
            WHERE c.tier = ? AND c.tour = ?
            GROUP BY c.champion_id ORDER BY n DESC LIMIT 50
            """,
            (tier, tour),
        )
    return {"tier": tier, "tour": tour, "metric": metric, "leaders": rows}


@router.get("/search")
def search(
    q: str = Query(..., min_length=2),
    tour: str | None = Query(None),
) -> dict:
    sql = "SELECT tour, player_id, full_name, ioc FROM players WHERE full_name LIKE ?"
    params: list = [f"%{q}%"]
    if tour:
        sql += " AND tour = ?"
        params.append(tour)
    sql += " ORDER BY full_name LIMIT 20"
    return {"q": q, "players": query(sql, tuple(params))}
