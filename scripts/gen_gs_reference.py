"""연도별 그랜드슬램 성적표 레퍼런스 생성기.

선수 상세 페이지의 "연도별 그랜드슬램 표"(performance timeline)에 쓸
레퍼런스 JSON 을 tennis.db 에서 추출한다.

대상: 그랜드슬램에서 16강(R16, round_order>=4) 이상 진출 기록이 있는 선수.
산출: data/reference/grand-slam-results/{tour}/{player_id}.json

셀 코드: W(우승) / F / SF / QF / 4R(R16) / 3R(R32) / 2R(R64) / 1R(R128) / A(불참) / NH(미개최)

사용법:
  python scripts/gen_gs_reference.py --all            # 자격 선수 전체
  python scripts/gen_gs_reference.py --name "Djokovic"  # 이름 부분일치
  python scripts/gen_gs_reference.py --tour atp --id 104925
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "tennis.db"
OUT_DIR = ROOT / "data" / "reference" / "grand-slam-results"

SLAMS = ["Australian Open", "Roland Garros", "Wimbledon", "US Open"]

# round_order(matches) → 셀 코드. 우승(F 승)은 별도 처리.
ROUND_CODE = {1: "1R", 2: "2R", 3: "3R", 4: "4R", 5: "QF", 6: "SF", 8: "F"}


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def qualifying_players(conn: sqlite3.Connection, tour: str) -> list[sqlite3.Row]:
    """GS R16+ 진출 기록 보유 선수."""
    return conn.execute(
        """
        SELECT p.player_id, p.full_name, p.ioc
        FROM players p
        WHERE p.tour = ? AND p.player_id IN (
          SELECT pid FROM (
            SELECT m.winner_id AS pid FROM matches m
              JOIN tournaments t ON t.tour=m.tour AND t.tourney_id=m.tourney_id
              WHERE t.tier='GS' AND m.tour=? AND m.round_order>=4
            UNION
            SELECT m.loser_id AS pid FROM matches m
              JOIN tournaments t ON t.tour=m.tour AND t.tourney_id=m.tourney_id
              WHERE t.tier='GS' AND m.tour=? AND m.round_order>=4
          )
        )
        ORDER BY p.full_name
        """,
        (tour, tour, tour),
    ).fetchall()


def build_timeline(conn: sqlite3.Connection, tour: str, pid: int) -> dict[str, dict[str, str]]:
    """{ "연도": { "대회명": 셀코드 } } — 선수의 GS 출전 전 기록."""
    rows = conn.execute(
        """
        SELECT t.season, t.name, m.round_order, m.round,
               (m.winner_id = ?) AS won
        FROM matches m
        JOIN tournaments t ON t.tour=m.tour AND t.tourney_id=m.tourney_id
        WHERE t.tier='GS' AND m.tour=? AND (m.winner_id=? OR m.loser_id=?)
        """,
        (pid, tour, pid, pid),
    ).fetchall()

    # 대회·연도별 '가장 깊은 라운드' 매치를 골라 셀 코드 산출.
    deepest: dict[tuple[int, str], sqlite3.Row] = {}
    for r in rows:
        key = (r["season"], r["name"])
        cur = deepest.get(key)
        if cur is None or r["round_order"] > cur["round_order"]:
            deepest[key] = r

    timeline: dict[str, dict[str, str]] = {}
    for (season, name), r in deepest.items():
        if r["round"] == "F" and r["won"]:
            code = "W"
        else:
            code = ROUND_CODE.get(r["round_order"], r["round"])
        timeline.setdefault(str(season), {})[name] = code
    return timeline


def gen_one(conn: sqlite3.Connection, tour: str, p: sqlite3.Row) -> dict:
    timeline = build_timeline(conn, tour, p["player_id"])
    return {
        "tour": tour,
        "player_id": p["player_id"],
        "full_name": p["full_name"],
        "ioc": p["ioc"],
        "slams": SLAMS,
        "results": dict(sorted(timeline.items())),
    }


def write(payload: dict) -> Path:
    out = OUT_DIR / payload["tour"] / f"{payload['player_id']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true", help="자격 선수 전체 생성")
    ap.add_argument("--name", help="이름 부분일치로 생성")
    ap.add_argument("--tour", choices=["atp", "wta"], help="--id 와 함께 사용")
    ap.add_argument("--id", type=int, help="단일 선수 player_id")
    args = ap.parse_args()

    conn = connect()
    tours = [args.tour] if args.tour else ["atp", "wta"]
    n = 0
    for tour in tours:
        if args.id is not None and args.tour == tour:
            players = conn.execute(
                "SELECT player_id, full_name, ioc FROM players WHERE tour=? AND player_id=?",
                (tour, args.id),
            ).fetchall()
        else:
            players = qualifying_players(conn, tour)
            if args.name:
                players = [p for p in players if args.name.lower() in (p["full_name"] or "").lower()]
            elif not args.all and args.id is None:
                continue  # 옵션 없으면 해당 tour 건너뜀

        for p in players:
            out = write(gen_one(conn, tour, p))
            n += 1
            if n <= 20 or args.all is False:
                print(f"  {out.relative_to(ROOT)}  ({p['full_name']})")
    conn.close()
    print(f"\n총 {n}개 생성 → {OUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
