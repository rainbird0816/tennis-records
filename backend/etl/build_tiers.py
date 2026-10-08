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

# 등급 시드는 2단: TD 라벨 자동 생성(td_supplement) → 수동 교정(tournament_tiers)이 우선.
TD_TIERS_CSV = SEED_DIR / "td_tournament_tiers.csv"
TIERS_CSV = SEED_DIR / "tournament_tiers.csv"

# 연말 왕중왕전 계보만. 'championships' 를 통째로 넣으면 'Soviet Championships'(WTA
# 1970-84 소련 선수권)·'Japanese Championships'(ATP 1969) 같은 일반 대회가 섞인다.
_FINALS_HINTS = (
    "finals", "masters cup", "tour finals", "tour championships",
    "virginia slims championships", "avon championships",
    "ginny championships", "wta championships", "tournament of champions",
)

# 팀 대항전·엑시비전 (단식 범위 밖, §1.5). tourney_level 'D' 로 안 잡히는 것들.
TEAM_EVENT_EXCLUDE = {
    "atp cup", "laver cup", "united cup", "hopman cup", "world team cup",
    "davis cup", "fed cup", "billie jean king cup",
}
# 개최지 이름으로만 적혀 있어 이름으로는 못 거르는 팀 대항전 — (tour, tourney_id 접미사).
# atp 615 = Dusseldorf ARAG 월드팀컵 (조별리그 + 결승 단식 2경기, 1982–2012).
TEAM_EVENT_IDS = {("atp", "615")}

# ATP 500 고정 셋 (2019+ 현행 기준, 이름 정규화 후 소문자). 나머지 tour-level 'A' = 250. (§1.2, Phase 4)
ATP_500_NAMES = {
    "rotterdam", "rio de janeiro", "dubai", "acapulco", "barcelona", "halle",
    "queen's club", "hamburg", "washington", "beijing", "tokyo", "vienna",
    "basel", "doha",
}
# ATP 500/250 분류 시작 시즌. 500/250 체계 출범(2009) 이후 전체 — Phase 4+5 통합.
# (500 고정셋은 현행 기준이라 2009–2013 Memphis/Valencia 등 일부는 250 으로 분류될 수 있음)
ATP_TOUR_MIN_SEASON = 2009

# WTA 'P' 레벨 중 실제 1000 인 비(非)PM 대회 (이름 기준, 2021+). PM 은 항상 1000.
# 등급 시드(td_tournament_tiers)가 있으면 그쪽이 먼저 적용되고, 여기는 폴백이다.
# Guadalajara 는 연도마다 250/500/1000 을 오가므로 이름 기준으로 못 쓴다 → 시드에 맡김.
WTA_1000_EXTRA = {"cincinnati", "montreal", "toronto", "wuhan"}


def load_seed_tiers() -> dict[tuple[str, int, str], str]:
    """(tour, season, name) → tier 매핑.

    1) `td_tournament_tiers.csv` — TD 등급 라벨에서 자동 생성 (2021+).
       연도별 승격/강등(Doha·Hamburg·Dallas·Munich, WTA Doha↔Dubai, Guadalajara…)을
       1차 소스의 level 코드로는 못 잡으므로 이걸로 덮는다.
    2) `tournament_tiers.csv` — 수동 교정. TD 라벨이 틀린 몇 건을 되돌린다 (우선).
    """
    mapping: dict[tuple[str, int, str], str] = {}
    for path, label in ((TD_TIERS_CSV, "TD"), (TIERS_CSV, "수동")):
        if not path.exists():
            print(f"[build_tiers] 시드 없음(스킵): {path}")
            continue
        n = 0
        with path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (row["tour"].strip(), int(row["season"]), row["name"].strip())
                mapping[key] = row["tier"].strip()
                n += 1
        print(f"[build_tiers] 시드 tier({label}) {n} 건 로드")
    return mapping


def derive_tier(
    *, tour: str, season: int, name: str, level_raw: str,
    seed_map: dict[tuple[str, int, str], str], tourney_id: str = "",
) -> str | None:
    """정규화 tier 도출. 매핑 불가 시 None (→ build_db 가 적재 제외)."""
    n = (name or "").lower()
    lvl = (level_raw or "").strip().upper()

    # 팀 대항전(Davis/Fed/BJK/United/ATP Cup, 월드팀컵) 제외 — 이름에 'Finals' 가
    # 있어도 단식 범위 밖 (§1.5). level 'D' 로 안 잡히는 것은 이름·id 로 거른다.
    if lvl == "D" or n in TEAM_EVENT_EXCLUDE:
        return None
    if (tour, str(tourney_id).rsplit("-", 1)[-1]) in TEAM_EVENT_IDS:
        return None

    if "olympic" in n:
        # 1968 멕시코시티는 시범·전시 종목(정식 메달 아님)이고 한 시즌에 두 대회가
        # 들어와 금메달이 2개로 집계된다 → 제외 (§12).
        if "demo" in n or "exhibition" in n:
            return None
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
        return "500" if n in ATP_500_NAMES else "250"

    return None


if __name__ == "__main__":
    m = load_seed_tiers()
    print(f"샘플: {list(m.items())[:5]}")
