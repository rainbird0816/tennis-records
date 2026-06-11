"""매치 디테일 라우터 (§7, §8).

GET /matches/{match_id}   세트별 스코어(match_sets) + 스탯(has_stats) + outcome
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..db import query, query_one

router = APIRouter()

# 스탯 대조 바 원천 컬럼 (§8)
_STAT_COLS = (
    "ace", "df", "svpt", "1stIn", "1stWon",
    "2ndWon", "SvGms", "bpSaved", "bpFaced",
)


@router.get("/matches/{match_id}")
def match_detail(match_id: str) -> dict:
    m = query_one("SELECT * FROM matches WHERE match_id = ?", (match_id,))
    if not m:
        raise HTTPException(404, "match not found")

    # 선수 이름 + 대회 메타 해석 (§8 헤더)
    players = {
        r["player_id"]: r
        for r in query(
            "SELECT player_id, full_name, ioc FROM players "
            "WHERE tour = ? AND player_id IN (?, ?)",
            (m["tour"], m["winner_id"], m["loser_id"]),
        )
    }
    names = {pid: r["full_name"] for pid, r in players.items()}
    tmeta = query_one(
        "SELECT name, tier, season, surface FROM tournaments "
        "WHERE tour = ? AND tourney_id = ?",
        (m["tour"], m["tourney_id"]),
    ) or {}

    sets = query(
        """
        SELECT set_no, w_games, l_games, tb_w, tb_l
        FROM match_sets WHERE match_id = ? ORDER BY set_no
        """,
        (match_id,),
    )

    stats = None
    if m.get("has_stats"):
        stats = {
            col: {"w": m.get(f"w_{col}"), "l": m.get(f"l_{col}")}
            for col in _STAT_COLS
        }

    return {
        "match_id": m["match_id"],
        "tour": m["tour"],
        "tourney_id": m["tourney_id"],
        "round": m["round"],
        "best_of": m["best_of"],
        "winner_id": m["winner_id"],
        "loser_id": m["loser_id"],
        "winner_name": names.get(m["winner_id"]),
        "loser_name": names.get(m["loser_id"]),
        "winner_ioc": (players.get(m["winner_id"]) or {}).get("ioc"),
        "loser_ioc": (players.get(m["loser_id"]) or {}).get("ioc"),
        "tournament_name": tmeta.get("name"),
        "tier": tmeta.get("tier"),
        "season": tmeta.get("season"),
        "surface": tmeta.get("surface"),
        "winner_seed": m["winner_seed"],
        "loser_seed": m["loser_seed"],
        "winner_rank": m["winner_rank"],
        "loser_rank": m["loser_rank"],
        "score": m["score"],
        "outcome": m["outcome"],
        "minutes": m["minutes"],
        "has_stats": bool(m["has_stats"]),
        "sets": sets,
        "stats": stats,
    }
