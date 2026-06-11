"""대회 라우터 (§7).

GET /tournaments/{tour}/{tourney_id}   대회 메타 + 라운드별 경기(브래킷)
GET /series/{slug}/champions?tour=     역대 우승자
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..db import query, query_one

router = APIRouter()


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
               wp.full_name AS champion_name, lp.full_name AS runnerup_name
        FROM champions c
        LEFT JOIN players wp ON wp.tour = c.tour AND wp.player_id = c.champion_id
        LEFT JOIN players lp ON lp.tour = c.tour AND lp.player_id = c.runnerup_id
        WHERE c.tour = ? AND c.name = ?
        ORDER BY c.season DESC
        """,
        (tour, slug),
    )
    return {"slug": slug, "tour": tour, "champions": champs}
