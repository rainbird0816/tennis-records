"""원천 CSV 다운로드 (PROJECT_BRIEF §6-1).

Jeff Sackmann tennis_atp / tennis_wta 의 연도별 매치 CSV + 선수 마스터를
data/raw/{atp,wta}/ 로 원샷 다운로드. API 키 불필요 (§0).

⚠️ 2026-06 이후 원본 리포지토리(JeffSackmann/tennis_atp·tennis_wta)가 비공개
처리돼 모든 URL 이 404 다. 과거 데이터는 아카이브 미러로 받고, **2026-06 이후
진행분은 미러에도 없으므로** `etl.td_supplement` (tennis-data.co.uk 보조 소스)로
채운다. (§13 데이터 리스크)

사용:
  python -m etl.fetch_sources                # 기본 연도범위
  python -m etl.fetch_sources --start 1968 --end 2024
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import RAW_DIR  # noqa: E402

RAW_BASE = {
    "atp": "https://raw.githubusercontent.com/JeffSackmann/tennis_atp/master",
    "wta": "https://raw.githubusercontent.com/JeffSackmann/tennis_wta/master",
}

# 1차 소스가 404 일 때 쓰는 아카이브 미러 (2026-06 스냅샷, 동일 파일명 / CC BY-NC-SA 4.0).
_MIRROR = "https://raw.githubusercontent.com/Aneeshers/tennis-sackmann-archive/main"
MIRROR_BASE = {"atp": f"{_MIRROR}/atp", "wta": f"{_MIRROR}/wta"}

# 선수 마스터 + 컬럼 사전 + 랭킹(연대별) 등 정적 파일
_RANK_DECADES = ["70s", "80s", "90s", "00s", "10s", "20s", "current"]
STATIC_FILES = {
    "atp": ["atp_players.csv", "matches_data_dictionary.txt"]
    + [f"atp_rankings_{d}.csv" for d in _RANK_DECADES],
    "wta": ["wta_players.csv"]
    + [f"wta_rankings_{d}.csv" for d in _RANK_DECADES],
}

# 연도별 매치 파일 패턴 (atp_matches_2023.csv / wta_matches_2023.csv)
MATCHES_PATTERN = "{tour}_matches_{year}.csv"

# ATP 1968~, WTA 도 동일 포맷 (적재 필터는 build_db 에서, §2.2)
DEFAULT_START = 1968
DEFAULT_END = 2026


def _download(url: str, dest: Path, *, tag: str = "", quiet_fail: bool = False) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310
            data = resp.read()
        dest.write_bytes(data)
        print(f"  ok   {dest.name}  ({len(data):,} B){tag}")
        return True
    except Exception as e:  # noqa: BLE001
        if not quiet_fail:
            print(f"  miss {dest.name}  ({e})")
        return False


def _download_with_mirror(tour: str, fname: str, dest: Path) -> bool:
    """1차 소스 → 실패 시 아카이브 미러. 이미 받아둔 파일은 미러 실패 시 보존."""
    if _download(f"{RAW_BASE[tour]}/{fname}", dest, quiet_fail=True):
        return True
    return _download(f"{MIRROR_BASE[tour]}/{fname}", dest, tag="  [mirror]")


def fetch(start: int, end: int) -> None:
    for tour in RAW_BASE:
        out = RAW_DIR / tour
        print(f"[{tour}] → {out}")
        for fname in STATIC_FILES[tour]:
            _download_with_mirror(tour, fname, out / fname)
        for year in range(start, end + 1):
            fname = MATCHES_PATTERN.format(tour=tour, year=year)
            _download_with_mirror(tour, fname, out / fname)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=DEFAULT_START)
    ap.add_argument("--end", type=int, default=DEFAULT_END)
    args = ap.parse_args()
    fetch(args.start, args.end)
