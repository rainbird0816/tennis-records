"""시즌별 랭킹 요약 적재 (Phase 7 — 랭킹 추이 차트용).

연대별 atp/wta_rankings_*.csv (주간 스냅샷)을 (tour, player, season) 으로 압축:
  - year_end_rank : 해당 시즌 마지막 랭킹일의 순위
  - best_rank     : 해당 시즌 최고(최저 숫자) 순위

연(年)은 한 연대 파일 안에 완결되므로 파일 단위 집계 후 합쳐도 정확.

주간 스냅샷이 끊긴 구간(1차 소스 중단 이후, §13)은 경기 단위 랭킹
(matches.winner_rank / loser_rank — 대회 시작 시점 순위)으로 보강한다.
스냅샷이 덮는 구간은 그대로 두므로 과거 시즌 값은 바뀌지 않는다.

build_db.py 이후 실행 (player_rankings 테이블이 이미 생성돼 있어야 함). 멱등.

사용:  python -m etl.build_rankings
"""
from __future__ import annotations

import glob
import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import DB_PATH, RAW_DIR  # noqa: E402


def _snapshot_end(tour: str) -> int:
    """주간 랭킹 스냅샷이 덮는 마지막 날짜 (YYYYMMDD). 없으면 0."""
    end = 0
    for fp in glob.glob(str(RAW_DIR / tour / f"{tour}_rankings_*.csv")):
        df = pd.read_csv(fp, usecols=["ranking_date"], low_memory=False)
        if len(df):
            end = max(end, int(df["ranking_date"].max()))
    return end


def _from_matches(conn: sqlite3.Connection, tour: str, after: int) -> pd.DataFrame:
    """스냅샷이 끊긴 이후 기간의 경기 단위 랭킹 → (player, season) 요약."""
    rows = conn.execute(
        """
        SELECT t.season,
               CASE WHEN s = 'w' THEN m.winner_id ELSE m.loser_id END AS player,
               CASE WHEN s = 'w' THEN m.winner_rank ELSE m.loser_rank END AS rnk,
               t.start_date
        FROM matches m
        JOIN tournaments t ON t.tour = m.tour AND t.tourney_id = m.tourney_id
        CROSS JOIN (SELECT 'w' AS s UNION ALL SELECT 'l') sides
        WHERE m.tour = ? AND CAST(t.start_date AS INTEGER) > ?
        """,
        (tour, after),
    ).fetchall()
    df = pd.DataFrame(rows, columns=["season", "player", "rank", "start_date"])
    df = df.dropna(subset=["player", "rank"])
    if df.empty:
        return pd.DataFrame(columns=["player", "season", "best_rank", "year_end_rank"])
    df = df.astype({"season": int, "player": int, "rank": int, "start_date": int})
    best = df.groupby(["player", "season"], as_index=False)["rank"].min()
    best = best.rename(columns={"rank": "best_rank"})
    last = df.loc[df.groupby(["player", "season"])["start_date"].idxmax(),
                  ["player", "season", "rank"]].rename(columns={"rank": "year_end_rank"})
    return best.merge(last, on=["player", "season"], how="outer")


def _aggregate(tour: str) -> pd.DataFrame:
    files = sorted(glob.glob(str(RAW_DIR / tour / f"{tour}_rankings_*.csv")))
    frames: list[pd.DataFrame] = []
    for fp in files:
        df = pd.read_csv(fp, usecols=["ranking_date", "rank", "player"], low_memory=False)
        df = df.dropna(subset=["ranking_date", "rank", "player"])
        df["season"] = (df["ranking_date"].astype("int64") // 10000).astype(int)
        df["player"] = df["player"].astype("int64")
        df["rank"] = df["rank"].astype("int64")

        best = df.groupby(["player", "season"], as_index=False)["rank"].min()
        best = best.rename(columns={"rank": "best_rank"})

        # 연말 = 시즌 내 가장 늦은 ranking_date 의 순위
        ye_idx = df.groupby(["player", "season"])["ranking_date"].idxmax()
        ye = df.loc[ye_idx, ["player", "season", "rank"]].rename(columns={"rank": "year_end_rank"})

        merged = best.merge(ye, on=["player", "season"], how="outer")
        frames.append(merged)

    if not frames:
        return pd.DataFrame(columns=["player", "season", "best_rank", "year_end_rank"])
    allf = pd.concat(frames, ignore_index=True)
    # 한 시즌이 여러 파일에 걸치는 경우는 없지만 안전하게 재집계
    out = allf.groupby(["player", "season"], as_index=False).agg(
        best_rank=("best_rank", "min"),
        year_end_rank=("year_end_rank", "last"),
    )
    out["tour"] = tour
    return out


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"먼저 build_db 실행 필요: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM player_rankings")
        total = 0
        for tour in ("atp", "wta"):
            df = _aggregate(tour)
            # 스냅샷 공백 구간 보강 — best 는 더 좋은 쪽, year_end 는 더 최근(경기) 쪽
            end = _snapshot_end(tour)
            extra = _from_matches(conn, tour, end)
            if not extra.empty:
                df = df.merge(extra, on=["player", "season"], how="outer",
                              suffixes=("", "_m"))
                df["best_rank"] = df[["best_rank", "best_rank_m"]].min(axis=1)
                df["year_end_rank"] = df["year_end_rank_m"].fillna(df["year_end_rank"])
                df = df.drop(columns=["best_rank_m", "year_end_rank_m"])
                n_fill = int(extra.player.nunique())
                print(f"[rankings] {tour}: 스냅샷 {end} 이후 경기로 선수 {n_fill:,} 명 보강")
            rows = [
                (tour, int(r.player), int(r.season),
                 None if pd.isna(r.year_end_rank) else int(r.year_end_rank),
                 None if pd.isna(r.best_rank) else int(r.best_rank))
                for r in df.itertuples(index=False)
            ]
            conn.executemany(
                "INSERT OR REPLACE INTO player_rankings VALUES (?,?,?,?,?)", rows
            )
            total += len(rows)
            print(f"[rankings] {tour}: {len(rows):,} 행 (선수×시즌)")
        conn.commit()
    finally:
        conn.close()
    print(f"[build_rankings] 완료 — 총 {total:,} 행")


if __name__ == "__main__":
    main()
