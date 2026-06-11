"""카테고리 라우터 (§7).

GET /categories                 6 카테고리 + (tier,tour) 가용/연도
GET /categories/{tier}?tour=    시리즈 대회 + latest_champion
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..config import TIERS
from ..db import query

router = APIRouter()


@router.get("/categories")
def list_categories() -> dict:
    """tier×tour 가용성 + 연도 범위. 프론트 토글 숨김 판단에 사용 (§9.3)."""
    rows = query(
        """
        SELECT tier, tour, MIN(season) AS min_season, MAX(season) AS max_season,
               COUNT(*) AS n_tournaments
        FROM tournaments
        WHERE tier IN ('GS','1000','500','250','FINALS','OLYMPICS')
        GROUP BY tier, tour
        """
    )
    by_tier: dict[str, dict] = {t: {"tier": t, "availability": []} for t in TIERS}
    for r in rows:
        by_tier[r["tier"]]["availability"].append(
            {
                "tour": r["tour"],
                "min_season": r["min_season"],
                "max_season": r["max_season"],
                "n_tournaments": r["n_tournaments"],
            }
        )
    return {"categories": list(by_tier.values())}


@router.get("/categories/{tier}")
def category_detail(
    tier: str,
    tour: str = Query(..., pattern="^(atp|wta)$"),
) -> dict:
    """해당 tier×tour 의 시리즈(대회 슬러그) 목록 + 각 최신 우승자."""
    if tier not in TIERS:
        raise HTTPException(404, f"unknown tier: {tier}")
    series = query(
        """
        SELECT t.name, COUNT(*) AS seasons,
               MIN(t.season) AS first_season, MAX(t.season) AS last_season,
               (SELECT t2.start_date FROM tournaments t2
                  WHERE t2.tour = t.tour AND t2.tier = t.tier AND t2.name = t.name
                  ORDER BY t2.season DESC LIMIT 1) AS latest_start_date
        FROM tournaments t
        WHERE t.tier = :tier AND t.tour = :tour
        GROUP BY t.name
        """,
        {"tier": tier, "tour": tour},
    )

    # 개최 시기(달력)순 정렬 — 대표 시즌 시작일의 MMDD 기준 (이름순 X).
    # GS 의 경우 자동으로 호주(01)→롤랑(05)→윔블던(06)→US(08) 순.
    def cal_key(s: dict) -> str:
        sd = s.get("latest_start_date") or ""
        return sd[4:8] if len(sd) >= 8 else "9999"  # MMDD, 없으면 뒤로

    for s in series:
        s["cal_mmdd"] = cal_key(s)
    series.sort(key=cal_key)

    # 시리즈별 최신 우승자 (§9.2). OLYMPICS 는 champions 뷰에 없어 비어 있음.
    latest: dict[str, dict] = {}
    for r in query(
        """
        SELECT c.name, c.season, c.tourney_id, c.champion_id,
               p.full_name AS champion_name
        FROM champions c
        LEFT JOIN players p ON p.tour = c.tour AND p.player_id = c.champion_id
        WHERE c.tier = :tier AND c.tour = :tour
        ORDER BY c.name, c.season DESC
        """,
        {"tier": tier, "tour": tour},
    ):
        latest.setdefault(
            r["name"],
            {
                "season": r["season"],
                "tourney_id": r["tourney_id"],
                "champion_id": r["champion_id"],
                "champion_name": r["champion_name"],
            },
        )
    for s in series:
        s["latest_champion"] = latest.get(s["name"])

    return {"tier": tier, "tour": tour, "series": series}
