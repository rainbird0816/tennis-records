"""올림픽 메달 추출 (PROJECT_BRIEF §6-4, §12).

식별: tournaments.tier == 'OLYMPICS'.
메달 규칙 (§12):
  - 금  = 결승(F) 승자
  - 은  = 결승(F) 패자
  - 동  = 동메달 결정전(BR) 승자.  BR 라운드가 없으면(초기 대회) 동메달 None 또는 SF 패자 처리.

build_db.py 이후 실행 (tennis.db 가 이미 있어야 함). 멱등.

사용:  python -m etl.build_olympics
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import DB_PATH  # noqa: E402


def build(conn: sqlite3.Connection) -> int:
    conn.execute("DELETE FROM olympic_medals")
    olympics = conn.execute(
        """
        SELECT tour, tourney_id, season
        FROM tournaments WHERE tier = 'OLYMPICS'
        """
    ).fetchall()

    rows: list[tuple] = []
    for tour, tourney_id, season in olympics:
        f = conn.execute(
            "SELECT winner_id, loser_id FROM matches "
            "WHERE tour=? AND tourney_id=? AND round='F'",
            (tour, tourney_id),
        ).fetchone()
        if f:
            rows.append((tour, season, "gold", f[0]))
            rows.append((tour, season, "silver", f[1]))
        br = conn.execute(
            "SELECT winner_id FROM matches "
            "WHERE tour=? AND tourney_id=? AND round='BR'",
            (tour, tourney_id),
        ).fetchone()
        if br:
            rows.append((tour, season, "bronze", br[0]))

    conn.executemany(
        "INSERT OR REPLACE INTO olympic_medals VALUES (?,?,?,?)", rows
    )
    conn.commit()
    return len(rows)


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"먼저 build_db 실행 필요: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        n = build(conn)
    finally:
        conn.close()
    print(f"[build_olympics] 메달 {n} 건 적재")


if __name__ == "__main__":
    main()
