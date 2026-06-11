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
        SELECT name, COUNT(*) AS seasons,
               MIN(season) AS first_season, MAX(season) AS last_season
        FROM tournaments
        WHERE tier = :tier AND tour = :tour
        GROUP BY name
        ORDER BY name
        """,
        {"tier": tier, "tour": tour},
    )

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
