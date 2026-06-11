"""tier 매핑 로더 (PROJECT_BRIEF §3, §6-2).

정규화 tier 도출:
  - name "Olympic*"        → OLYMPICS
  - tourney_level == 'G'   → GS
  - 파이널스(Finals/WTA Championships/Tour Finals) → FINALS
  - tourney_level == 'M'   → 1000  (ATP Masters)
  - 그 외 (WTA 2021+ 등급)  → data/seed/tournament_tiers.csv 큐레이션 참조

WTA 1000/500/250 은 2021+ 만 적재 대상이므로 시드 CSV 로 (tour,season,name)→tier 매핑.
ATP pre-2009 / WTA Premier·Tier 백필은 보류 (§3, §13).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import SEED_DIR  # noqa: E402

TIERS_CSV = SEED_DIR / "tournament_tiers.csv"

_FINALS_HINTS = ("finals", "championships", "masters cup", "tour finals")


def load_seed_tiers() -> dict[tuple[str, int, str], str]:
    """(tour, season, name) → tier 매핑 (WTA 2021+ 등급 큐레이션)."""
    mapping: dict[tuple[str, int, str], str] = {}
    if not TIERS_CSV.exists():
        print(f"[build_tiers] 시드 없음(스킵): {TIERS_CSV}")
        return mapping
    with TIERS_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["tour"].strip(), int(row["season"]), row["name"].strip())
            mapping[key] = row["tier"].strip()
    print(f"[build_tiers] 시드 tier {len(mapping)} 건 로드")
    return mapping


def derive_tier(
    *, tour: str, season: int, name: str, level_raw: str,
    seed_map: dict[tuple[str, int, str], str],
) -> str | None:
    """정규화 tier 도출. 매핑 불가 시 None (→ build_db 가 적재 제외)."""
    n = (name or "").lower()
    lvl = (level_raw or "").strip().upper()

    # 팀 대항전(Davis/Fed/BJK Cup) 제외 — 이름에 'Finals' 가 있어도 단식 범위 밖 (§1.5)
    if lvl == "D":
        return None

    if "olympic" in n:
        return "OLYMPICS"
    if lvl == "G":
        return "GS"
    # Tour Finals: tourney_level 'F' (안정적) 또는 대회명 힌트
    if lvl == "F" or any(h in n for h in _FINALS_HINTS):
        return "FINALS"
    if lvl == "M":  # ATP Masters 1000
        return "1000"
    # WTA 등급 등은 시드 큐레이션에 의존
    return seed_map.get((tour, season, name))


if __name__ == "__main__":
    m = load_seed_tiers()
    print(f"샘플: {list(m.items())[:5]}")
