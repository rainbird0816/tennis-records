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

# ATP 500 고정 셋 (2019+ 현행 기준, 이름 정규화 후 소문자). 나머지 tour-level 'A' = 250. (§1.2, Phase 4)
ATP_500_NAMES = {
    "rotterdam", "rio de janeiro", "dubai", "acapulco", "barcelona", "halle",
    "queen's club", "hamburg", "washington", "beijing", "tokyo", "vienna",
    "basel", "doha",
}
# 팀/엑시비전 (단식 범위 밖, §1.5) — level 'A' 로 새어 들어옴
ATP_TEAM_EXCLUDE = {"atp cup", "laver cup", "united cup"}
# ATP 500/250 분류 시작 시즌. 500/250 체계 출범(2009) 이후 전체 — Phase 4+5 통합.
# (500 고정셋은 현행 기준이라 2009–2013 Memphis/Valencia 등 일부는 250 으로 분류될 수 있음)
ATP_TOUR_MIN_SEASON = 2009

# WTA 'P' 레벨 중 실제 1000 인 비(非)PM 대회 (이름 기준, 2021+). PM 은 항상 1000.
WTA_1000_EXTRA = {"cincinnati", "montreal", "toronto", "wuhan", "guadalajara"}


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

    # 시드 큐레이션이 있으면 최우선 (WTA 1000 등 수동 지정)
    seeded = seed_map.get((tour, season, name))
    if seeded:
        return seeded

    # WTA 등급 (2021+; season 필터는 build_db 에서) — tourney_level 코드 기반 (§3)
    if tour == "wta":
        if lvl == "PM" or n in WTA_1000_EXTRA:
            return "1000"
        if lvl == "P":
            return "500"
        if lvl in ("I", "W"):
            return "250"
        return None

    # ATP 500/250 (2019+; tour-level 'A') — 500 고정셋 외 나머지는 250 (§1.2)
    if tour == "atp" and lvl == "A" and season >= ATP_TOUR_MIN_SEASON:
        if n in ATP_TEAM_EXCLUDE:
            return None
        return "500" if n in ATP_500_NAMES else "250"

    return None


if __name__ == "__main__":
    m = load_seed_tiers()
    print(f"샘플: {list(m.items())[:5]}")
