"""메인 ETL: 원천 CSV → 정규화 → tennis.db (PROJECT_BRIEF §6-3).

- (tour, player_id) 복합키로 ATP/WTA player_id 충돌 회피 (§2.2, §12).
- WTA 1000/500/250 은 season >= 2021 만 적재 (§2.2 옵션 B).
- score 파서 → match_sets, outcome, has_stats(1991+) (§1.3, §6).
- 멱등: 매 실행마다 스키마 재적용 후 재적재 (§6 규칙).

원천 CSV 본문은 모델 컨텍스트에 올리지 않는다 (§0). head/요약만.

사용:  python -m etl.build_db
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import (  # noqa: E402
    ATP_1000_MIN_SEASON,
    DB_PATH,
    RAW_DIR,
    STATS_MIN_SEASON,
    WTA_GRADE_MIN_SEASON,
)
from etl.build_tiers import derive_tier, load_seed_tiers  # noqa: E402
from etl.score_parser import parse_score  # noqa: E402

SCHEMA_SQL = Path(__file__).with_name("schema.sql")

ROUND_ORDER = {
    "RR": 0, "R128": 1, "R64": 2, "R32": 3, "R16": 4,
    "QF": 5, "SF": 6, "BR": 7, "F": 8,  # BR = 동메달전(올림픽)
}

STAT_COLS = [
    "ace", "df", "svpt", "1stIn", "1stWon",
    "2ndWon", "SvGms", "bpSaved", "bpFaced",
]

# 대회명 정규화: 연도별 표기 흔들림을 같은 시리즈로 합침 (§12 이름 정합).
# 1977 Australian Open-2 같은 '실제 별도 개최'는 유지.
_NAME_CANON = {
    "us open": "US Open",
    "australian chps.": "Australian Open",
    "australian championships": "Australian Open",
    # 1977 년 1·12월 두 번 열린 호주오픈 → 같은 시리즈로 통합
    "australian open-2": "Australian Open",
    "australian open 2": "Australian Open",
    # ATP 연말 왕중왕전 계보 통합 (Masters Cup 2000–2008 = Tour Finals)
    "masters cup": "Tour Finals",
    # Next Gen Finals 표기 흔들림 통합
    "nextgen finals": "Next Gen Finals",
    # 500/250 대회명 표기 흔들림 (Phase 4)
    "atp rio de janeiro": "Rio de Janeiro",
    "rio de janeiro": "Rio de Janeiro",
    "st petersburg": "St. Petersburg",
    "st. petersburg": "St. Petersburg",
}


def canonical_name(name: str) -> str:
    return _NAME_CANON.get((name or "").strip().lower(), name)


def _i(v) -> int | None:
    """NaN/빈값 안전 int 변환."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _season_from_date(tourney_date) -> int | None:
    s = str(_i(tourney_date) or "")
    return int(s[:4]) if len(s) >= 4 else None


def apply_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))


def load_players(conn: sqlite3.Connection, tour: str) -> None:
    path = RAW_DIR / tour / f"{tour}_players.csv"
    if not path.exists():
        print(f"[players] 없음(스킵): {path}")
        return
    df = pd.read_csv(path, low_memory=False)
    cols = {c.lower(): c for c in df.columns}

    def col(name: str):
        return df[cols[name]] if name in cols else None

    name = (df[cols["name_first"]].fillna("") + " " + df[cols["name_last"]].fillna("")
            ).str.strip() if "name_first" in cols else col("name")
    rows = []
    for i in range(len(df)):
        pid = _i(df[cols["player_id"]].iloc[i])
        if pid is None:
            continue
        ht = _i(col("height").iloc[i]) if "height" in cols else None
        wid = col("wikidata_id").iloc[i] if "wikidata_id" in cols else None
        wid = str(wid) if wid is not None and pd.notna(wid) else None
        rows.append((
            tour, pid,
            str(name.iloc[i]) if name is not None else None,
            (str(col("hand").iloc[i]) if "hand" in cols else None),
            (str(_i(col("dob").iloc[i])) if "dob" in cols else None),
            (str(col("ioc").iloc[i]) if "ioc" in cols else None),
            ht, wid,
        ))
    conn.executemany(
        "INSERT OR REPLACE INTO players VALUES (?,?,?,?,?,?,?,?)", rows
    )
    print(f"[players] {tour}: {len(rows):,} 명")


def _is_wta_grade(tier: str) -> bool:
    return tier in ("1000", "500", "250")


def load_matches(conn: sqlite3.Connection, tour: str, seed_map: dict) -> None:
    files = sorted((RAW_DIR / tour).glob(f"{tour}_matches_*.csv"))
    if not files:
        print(f"[matches] 연도 파일 없음(스킵): {RAW_DIR / tour}")
        return

    seen_tourneys: set[str] = set()
    n_matches = n_sets = n_skipped = 0

    for fp in files:
        df = pd.read_csv(fp, low_memory=False)
        cols = {c.lower(): c for c in df.columns}

        def g(row, name):
            key = name.lower()  # cols 키는 소문자; w_1stIn 등 대소문자 혼합 대응
            return row[cols[key]] if key in cols else None

        t_rows, m_rows, s_rows = [], [], []
        for _, row in df.iterrows():
            tourney_id = str(g(row, "tourney_id"))
            name_ = canonical_name(str(g(row, "tourney_name")))
            season = _season_from_date(g(row, "tourney_date"))
            level_raw = str(g(row, "tourney_level") or "")
            if season is None:
                continue

            tier = derive_tier(
                tour=tour, season=season, name=name_,
                level_raw=level_raw, seed_map=seed_map,
            )
            if tier is None:
                n_skipped += 1
                continue
            # WTA 등급(1000/500/250)은 2021+ 만 (§2.2)
            if tour == "wta" and _is_wta_grade(tier) and season < WTA_GRADE_MIN_SEASON:
                n_skipped += 1
                continue
            # ATP 1000 은 마스터스 시리즈 출범(1990) 이후만 (§1.2)
            if tour == "atp" and tier == "1000" and season < ATP_1000_MIN_SEASON:
                n_skipped += 1
                continue

            if tourney_id not in seen_tourneys:
                seen_tourneys.add(tourney_id)
                t_rows.append((
                    tour, tourney_id, name_, tier, level_raw,
                    str(g(row, "surface") or ""), _i(g(row, "draw_size")),
                    season, str(_i(g(row, "tourney_date")) or ""),
                    None, None,  # location, country → 위키 큐레이션 보조(§2.4)
                ))

            match_num = _i(g(row, "match_num"))
            match_id = f"{tour}-{tourney_id}-{match_num}"
            rnd = str(g(row, "round") or "")
            score = g(row, "score")
            outcome, sets = parse_score(score if isinstance(score, str) else None)
            has_stats = 1 if (season >= STATS_MIN_SEASON and _i(g(row, "w_svpt")) is not None) else 0

            stat_vals = []
            for side in ("w", "l"):
                for c in STAT_COLS:
                    stat_vals.append(_i(g(row, f"{side}_{c}")))

            m_rows.append((
                match_id, tour, tourney_id, match_num,
                rnd, ROUND_ORDER.get(rnd, 99), _i(g(row, "best_of")),
                _i(g(row, "winner_id")), _i(g(row, "loser_id")),
                _i(g(row, "winner_seed")), _i(g(row, "loser_seed")),
                _i(g(row, "winner_rank")), _i(g(row, "loser_rank")),
                str(score) if isinstance(score, str) else None,
                outcome, _i(g(row, "minutes")), has_stats,
                *stat_vals,
            ))
            for s in sets:
                s_rows.append((match_id, s["set_no"], s["w_games"],
                               s["l_games"], s["tb_w"], s["tb_l"]))

        if t_rows:
            conn.executemany(
                "INSERT OR REPLACE INTO tournaments VALUES (" + ",".join("?" * 11) + ")",
                t_rows,
            )
        if m_rows:
            conn.executemany(
                "INSERT OR REPLACE INTO matches VALUES (" + ",".join("?" * 35) + ")",
                m_rows,
            )
        if s_rows:
            conn.executemany(
                "INSERT OR REPLACE INTO match_sets VALUES (?,?,?,?,?,?)", s_rows
            )
        n_matches += len(m_rows)
        n_sets += len(s_rows)

    print(f"[matches] {tour}: 경기 {n_matches:,} / 세트 {n_sets:,} / 제외 {n_skipped:,}")


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    seed_map = load_seed_tiers()
    conn = sqlite3.connect(DB_PATH)
    try:
        apply_schema(conn)
        for tour in ("atp", "wta"):
            load_players(conn, tour)
            load_matches(conn, tour, seed_map)
        conn.commit()
    finally:
        conn.close()
    print(f"[build_db] 완료 → {DB_PATH}")


if __name__ == "__main__":
    main()
