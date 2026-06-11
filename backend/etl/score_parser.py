"""score 문자열 → 세트별 게임 스코어 + 타이브레이크 + outcome 파서 (PROJECT_BRIEF §6).

Sackmann 데이터의 `score` 컬럼은 **경기 승자 관점**으로 적힌다.
  예) "6-4 3-6 7-6(5)"  → 승자가 1·3세트, 패자가 2세트.

규칙 (§6, §12):
- 공백으로 세트 분리, 각 세트는 `W-L` (+ 선택 `(tb)`).
- 괄호 안 숫자 = **그 세트 패자의 타이브레이크 득점**. (`(5)` → 7-5, `(8-6)` → 명시형)
- 토큰 `RET` / `W/O`(`WO`) / `DEF` 를 만나면 `outcome` 설정 후 이후 파싱 중단.
- 어드밴티지 최종세트(타이브레이크 없는 `70-68` 등)·미완 세트 허용.
- 파싱 불가 토큰은 건너뛰되, 전부 실패하면 outcome 만 반환.

반환: (outcome, sets)
  outcome ∈ {"completed", "RET", "W/O", "DEF"}
  sets    = [{set_no, w_games, l_games, tb_w, tb_l}, ...]
            게임/타이브레이크 모두 **경기 승자/패자 기준** (tb 없으면 None).
"""
from __future__ import annotations

import re
from typing import NamedTuple, Optional

_RETIRE_TOKENS = {
    "RET": "RET", "RET.": "RET", "RETIRED": "RET",
    "W/O": "W/O", "WO": "W/O", "WALKOVER": "W/O",
    "DEF": "DEF", "DEF.": "DEF",
    "ABD": "RET", "ABN": "RET",  # abandoned → 기권 취급
}

# "6-4", "7-6(5)", "7-6(8-6)", "70-68"
_SET_RE = re.compile(r"^(\d{1,2})-(\d{1,2})(?:\((\d{1,2})(?:-(\d{1,2}))?\))?$")


class ParsedSet(NamedTuple):
    set_no: int
    w_games: int
    l_games: int
    tb_w: Optional[int]
    tb_l: Optional[int]


def _winner_tb_points(loser_pts: int) -> int:
    """타이브레이크 패자 득점 → 승자 득점 추정 (2점차 마감)."""
    return 7 if loser_pts <= 5 else loser_pts + 2


def _parse_set(token: str, set_no: int) -> Optional[ParsedSet]:
    m = _SET_RE.match(token)
    if not m:
        return None
    w_games, l_games = int(m.group(1)), int(m.group(2))

    tb_w = tb_l = None
    if m.group(3) is not None:
        if m.group(4) is not None:
            # 명시형 (a-b): a-b 는 그 세트 '승자-패자' 의 TB 득점
            set_winner_tb, set_loser_tb = int(m.group(3)), int(m.group(4))
        else:
            # 약식 (n): n = 세트 패자의 TB 득점, 승자는 추정
            set_loser_tb = int(m.group(3))
            set_winner_tb = _winner_tb_points(set_loser_tb)

        # 세트 승자가 곧 TB 승자. 경기 승자/패자 관점으로 매핑.
        if w_games >= l_games:  # 경기 승자가 이 세트도 승
            tb_w, tb_l = set_winner_tb, set_loser_tb
        else:                   # 경기 승자가 이 세트를 패
            tb_w, tb_l = set_loser_tb, set_winner_tb

    return ParsedSet(set_no, w_games, l_games, tb_w, tb_l)


def parse_score(score: Optional[str]) -> tuple[str, list[dict]]:
    """score 문자열 파싱. (outcome, sets[dict]) 반환."""
    outcome = "completed"
    sets: list[dict] = []

    if not score or not str(score).strip():
        # 빈 score: 보통 W/O. 세트 없음.
        return "W/O", sets

    tokens = str(score).strip().split()
    set_no = 0
    for raw in tokens:
        upper = raw.upper().strip(".,;")
        if upper in _RETIRE_TOKENS:
            outcome = _RETIRE_TOKENS[upper]
            break  # 이후 세트 중단 (§6)

        # "6-4(RET)" 같은 결합 토큰 방지용: 순수 세트 토큰만 시도
        set_no += 1
        parsed = _parse_set(raw, set_no)
        if parsed is None:
            # 알 수 없는 토큰 — 세트 카운트 롤백 후 건너뜀
            set_no -= 1
            continue
        sets.append(parsed._asdict())

    # score 가 기권 토큰만 있고 세트가 전혀 없으면 W/O 로 본다
    if not sets and outcome == "completed":
        outcome = "W/O"

    return outcome, sets


def format_set(s: dict) -> str:
    """디버그/검증용: 한 세트를 사람이 읽을 문자열로."""
    base = f"{s['w_games']}-{s['l_games']}"
    if s.get("tb_w") is not None:
        base += f"({s['tb_w']}-{s['tb_l']})"
    return base
