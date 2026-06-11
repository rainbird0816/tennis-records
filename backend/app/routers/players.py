"""선수 라우터 (§7, §9.4).

GET /players/{tour}/{player_id}          프로필 + 통산 승패
GET /players/{tour}/{player_id}/titles   우승 목록 (tier 필터 선택)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..db import query, query_one

router = APIRouter()


@router.get("/players/{tour}/{player_id}")
def player_profile(tour: str, player_id: int) -> dict:
    p = query_one(
        "SELECT * FROM players WHERE tour = ? AND player_id = ?",
        (tour, player_id),
    )
    if not p:
        raise HTTPException(404, "player not found")

    rec = query_one(
        """
        SELECT
          SUM(CASE WHEN winner_id = :pid THEN 1 ELSE 0 END) AS wins,
          SUM(CASE WHEN loser_id  = :pid THEN 1 ELSE 0 END) AS losses
        FROM matches
        WHERE tour = :tour AND (winner_id = :pid OR loser_id = :pid)
        """,
        {"tour": tour, "pid": player_id},
    )
    return {"player": p, "record": rec}


@router.get("/players/{tour}/{player_id}/titles")
def player_titles(
    tour: str,
    player_id: int,
    tier: str | None = Query(None),
) -> dict:
    sql = """
        SELECT season, name, tier, surface, runnerup_id, score
        FROM champions
        WHERE tour = ? AND champion_id = ?
    """
    params: list = [tour, player_id]
    if tier:
        sql += " AND tier = ?"
        params.append(tier)
    sql += " ORDER BY season DESC"
    return {"tour": tour, "player_id": player_id, "titles": query(sql, tuple(params))}
