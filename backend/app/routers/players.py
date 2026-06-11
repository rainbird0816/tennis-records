"""선수 라우터 (§7, §9.4).

GET /players/{tour}/{player_id}          프로필 + 통산 + 서피스별 + 플레이스타일(데이터 기반)
GET /players/{tour}/{player_id}/career   tier별 우승/결승 + 서피스 + 스타일 지표
GET /players/{tour}/{player_id}/titles   우승 목록 (tier 필터 선택)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..db import query, query_one

router = APIRouter()

_TIER_ORDER = {"GS": 0, "1000": 1, "FINALS": 2, "500": 3, "250": 4, "OLYMPICS": 5}


def _record(tour: str, pid: int) -> dict:
    return query_one(
        """
        SELECT
          SUM(CASE WHEN winner_id = :pid THEN 1 ELSE 0 END) AS wins,
          SUM(CASE WHEN loser_id  = :pid THEN 1 ELSE 0 END) AS losses
        FROM matches
        WHERE tour = :tour AND (winner_id = :pid OR loser_id = :pid)
        """,
        {"tour": tour, "pid": pid},
    ) or {"wins": 0, "losses": 0}


def _by_surface(tour: str, pid: int) -> list[dict]:
    rows = query(
        """
        SELECT t.surface,
          SUM(CASE WHEN m.winner_id = :pid THEN 1 ELSE 0 END) AS wins,
          SUM(CASE WHEN m.loser_id  = :pid THEN 1 ELSE 0 END) AS losses
        FROM matches m
        JOIN tournaments t ON t.tour = m.tour AND t.tourney_id = m.tourney_id
        WHERE m.tour = :tour AND (m.winner_id = :pid OR m.loser_id = :pid)
          AND t.surface IS NOT NULL AND t.surface <> ''
        GROUP BY t.surface ORDER BY wins DESC
        """,
        {"tour": tour, "pid": pid},
    )
    for r in rows:
        tot = (r["wins"] or 0) + (r["losses"] or 0)
        r["pct"] = round(100 * (r["wins"] or 0) / tot, 1) if tot else None
    return rows


def _style(tour: str, pid: int) -> dict | None:
    """플레이스타일 = 스탯 보유 경기(1991+)의 서브 지표 집계 + 파생 라벨."""
    s = query_one(
        """
        SELECT
          COUNT(*) AS matches,
          SUM(CASE WHEN winner_id=:pid THEN w_ace    ELSE l_ace    END) AS ace,
          SUM(CASE WHEN winner_id=:pid THEN w_df     ELSE l_df     END) AS df,
          SUM(CASE WHEN winner_id=:pid THEN w_svpt   ELSE l_svpt   END) AS svpt,
          SUM(CASE WHEN winner_id=:pid THEN w_1stIn  ELSE l_1stIn  END) AS first_in,
          SUM(CASE WHEN winner_id=:pid THEN w_1stWon ELSE l_1stWon END) AS first_won,
          SUM(CASE WHEN winner_id=:pid THEN w_2ndWon ELSE l_2ndWon END) AS second_won,
          SUM(CASE WHEN winner_id=:pid THEN w_bpSaved ELSE l_bpSaved END) AS bp_saved,
          SUM(CASE WHEN winner_id=:pid THEN w_bpFaced ELSE l_bpFaced END) AS bp_faced
        FROM matches
        WHERE tour=:tour AND (winner_id=:pid OR loser_id=:pid) AND has_stats=1
        """,
        {"tour": tour, "pid": pid},
    )
    if not s or not s["matches"] or not s["svpt"]:
        return None

    svpt = s["svpt"]
    first_in = s["first_in"] or 0
    second_pts = svpt - first_in
    pct = lambda a, b: round(100 * (a or 0) / b, 1) if b else None  # noqa: E731

    style = {
        "matches": s["matches"],
        "ace_pct": pct(s["ace"], svpt),
        "df_pct": pct(s["df"], svpt),
        "first_in_pct": pct(first_in, svpt),
        "first_win_pct": pct(s["first_won"], first_in),
        "second_win_pct": pct(s["second_won"], second_pts),
        "bp_saved_pct": pct(s["bp_saved"], s["bp_faced"]),
    }
    # 데이터 기반 파생 라벨
    labels: list[str] = []
    if (style["ace_pct"] or 0) >= 8:
        labels.append("강서브")
    if (style["first_win_pct"] or 0) >= 75:
        labels.append("막강 1st 서브")
    if (style["second_win_pct"] or 0) >= 52:
        labels.append("안정적 2nd 서브")
    if (style["bp_saved_pct"] or 0) >= 65:
        labels.append("BP 위기관리")
    style["labels"] = labels
    return style


def _by_tier(tour: str, pid: int) -> list[dict]:
    rows = query(
        """
        SELECT t.tier,
          SUM(CASE WHEN m.round='F' AND m.winner_id=:pid THEN 1 ELSE 0 END) AS titles,
          SUM(CASE WHEN m.round='F' AND m.loser_id =:pid THEN 1 ELSE 0 END) AS runner_ups,
          SUM(CASE WHEN m.round='SF' AND m.loser_id=:pid THEN 1 ELSE 0 END) AS sf_exits
        FROM matches m
        JOIN tournaments t ON t.tour = m.tour AND t.tourney_id = m.tourney_id
        WHERE m.tour=:tour AND (m.winner_id=:pid OR m.loser_id=:pid)
        GROUP BY t.tier
        """,
        {"tour": tour, "pid": pid},
    )
    for r in rows:
        r["finals"] = (r["titles"] or 0) + (r["runner_ups"] or 0)
    rows.sort(key=lambda r: _TIER_ORDER.get(r["tier"], 9))
    return [r for r in rows if r["finals"] or r["sf_exits"]]


@router.get("/players/{tour}/{player_id}")
def player_profile(tour: str, player_id: int) -> dict:
    p = query_one(
        "SELECT * FROM players WHERE tour = ? AND player_id = ?",
        (tour, player_id),
    )
    if not p:
        raise HTTPException(404, "player not found")
    return {
        "player": p,
        "record": _record(tour, player_id),
        "by_surface": _by_surface(tour, player_id),
        "style": _style(tour, player_id),
        "by_tier": _by_tier(tour, player_id),
    }


@router.get("/players/{tour}/{player_id}/titles")
def player_titles(
    tour: str,
    player_id: int,
    tier: str | None = Query(None),
) -> dict:
    sql = """
        SELECT season, name, tier, surface, runnerup_id, score, tourney_id
        FROM champions
        WHERE tour = ? AND champion_id = ?
    """
    params: list = [tour, player_id]
    if tier:
        sql += " AND tier = ?"
        params.append(tier)
    sql += " ORDER BY season DESC"
    return {"tour": tour, "player_id": player_id, "titles": query(sql, tuple(params))}
