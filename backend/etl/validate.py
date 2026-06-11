"""정합성 리포트 (PROJECT_BRIEF §6-5, §12 체크리스트).

행수 · 우승자/메달 · 라운드 · tier · 세트합 정합성을 점검해 출력.
실패가 아니라 '리포트' — 의심 케이스를 사람이 보고 판단.

사용:  python -m etl.validate
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import DB_PATH  # noqa: E402


def _section(title: str) -> None:
    print(f"\n── {title} " + "─" * max(0, 40 - len(title)))


def run(conn: sqlite3.Connection) -> None:
    q = lambda sql: conn.execute(sql).fetchall()  # noqa: E731

    _section("행수")
    for tbl in ("players", "tournaments", "matches", "match_sets", "olympic_medals"):
        try:
            (n,) = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()
            print(f"  {tbl:16} {n:>10,}")
        except sqlite3.OperationalError:
            print(f"  {tbl:16} (없음)")

    _section("tier × tour 분포")
    for tour, tier, season_lo, season_hi, n in q(
        """SELECT tour, tier, MIN(season), MAX(season), COUNT(*)
           FROM tournaments GROUP BY tour, tier ORDER BY tour, tier"""
    ):
        print(f"  {tour} {tier:8} {season_lo}-{season_hi}  대회 {n:,}")

    _section("결승 1개 초과/누락 대회 (의심)")
    bad = q(
        """SELECT tour, tourney_id, COUNT(*) c FROM matches
           WHERE round='F' GROUP BY tour, tourney_id HAVING c <> 1
           LIMIT 20"""
    )
    print(f"  {len(bad)} 건 (표시 최대 20):")
    for tour, tid, c in bad:
        print(f"    {tour} {tid}: F {c} 개")

    _section("score 있으나 세트 0개 (W/O 제외)")
    (n,) = conn.execute(
        """SELECT COUNT(*) FROM matches m
           WHERE m.score IS NOT NULL AND m.outcome <> 'W/O'
             AND NOT EXISTS (SELECT 1 FROM match_sets s WHERE s.match_id=m.match_id)"""
    ).fetchone()
    print(f"  {n:,} 건")

    _section("outcome 분포")
    for outcome, n in q(
        "SELECT outcome, COUNT(*) FROM matches GROUP BY outcome ORDER BY 2 DESC"
    ):
        print(f"  {str(outcome):10} {n:>10,}")

    _section("has_stats 비율")
    row = conn.execute(
        "SELECT SUM(has_stats), COUNT(*) FROM matches"
    ).fetchone()
    if row and row[1]:
        print(f"  {row[0]:,} / {row[1]:,}  ({100*row[0]/row[1]:.1f}%)")

    _section("올림픽 메달")
    for tour, season, medal, pid in q(
        "SELECT tour, season, medal, player_id FROM olympic_medals "
        "ORDER BY season, tour LIMIT 30"
    ):
        print(f"  {season} {tour} {medal:6} → {pid}")


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"먼저 build_db 실행 필요: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        run(conn)
    finally:
        conn.close()
    print("\n[validate] 리포트 완료")


if __name__ == "__main__":
    main()
