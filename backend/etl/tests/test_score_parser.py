"""score_parser 단위 테스트 (PROJECT_BRIEF §6, §12 체크리스트).

실행:  cd backend && pytest etl/tests -q
"""
from __future__ import annotations

import pytest

from etl.score_parser import parse_score


def test_straight_sets():
    outcome, sets = parse_score("6-4 6-3")
    assert outcome == "completed"
    assert sets == [
        {"set_no": 1, "w_games": 6, "l_games": 4, "tb_w": None, "tb_l": None},
        {"set_no": 2, "w_games": 6, "l_games": 3, "tb_w": None, "tb_l": None},
    ]


def test_tiebreak_shorthand():
    # (5) → 패자 5점, 승자 7점
    outcome, sets = parse_score("7-6(5) 6-4")
    assert outcome == "completed"
    assert sets[0] == {"set_no": 1, "w_games": 7, "l_games": 6, "tb_w": 7, "tb_l": 5}


def test_tiebreak_extended_shorthand():
    # (8) → 패자 8점, 승자 10점 (2점차)
    _, sets = parse_score("7-6(8)")
    assert sets[0]["tb_w"] == 10 and sets[0]["tb_l"] == 8


def test_tiebreak_explicit_form():
    _, sets = parse_score("6-4 3-6 7-6(10-8)")
    assert sets[2] == {"set_no": 3, "w_games": 7, "l_games": 6, "tb_w": 10, "tb_l": 8}


def test_set_lost_by_match_winner_tiebreak_mapping():
    # 경기 승자가 2세트를 6-7로 패 → tb 는 승자 관점에서 작은 값
    _, sets = parse_score("6-4 6-7(5) 6-2")
    s2 = sets[1]
    assert s2["w_games"] == 6 and s2["l_games"] == 7
    # 세트 패자(=경기 승자) TB 득점 5, 세트 승자(=경기 패자) 7
    assert s2["tb_w"] == 5 and s2["tb_l"] == 7


def test_retirement():
    outcome, sets = parse_score("6-2 3-6 6-4 RET")
    assert outcome == "RET"
    # RET 이후 중단, 앞선 3세트만
    assert len(sets) == 3


def test_retirement_mid_match():
    outcome, sets = parse_score("6-1 2-1 RET")
    assert outcome == "RET"
    assert sets == [
        {"set_no": 1, "w_games": 6, "l_games": 1, "tb_w": None, "tb_l": None},
        {"set_no": 2, "w_games": 2, "l_games": 1, "tb_w": None, "tb_l": None},
    ]


def test_walkover_empty():
    outcome, sets = parse_score("W/O")
    assert outcome == "W/O" and sets == []


def test_walkover_blank():
    for blank in ["", "   ", None]:
        outcome, sets = parse_score(blank)
        assert outcome == "W/O" and sets == []


def test_default():
    outcome, sets = parse_score("DEF")
    assert outcome == "DEF" and sets == []


def test_advantage_final_set_no_tiebreak():
    # 어드밴티지 최종세트 (타이브레이크 없는 70-68) — §6/§12
    _, sets = parse_score("6-7(3) 7-6(5) 70-68")
    assert sets[2] == {
        "set_no": 3, "w_games": 70, "l_games": 68, "tb_w": None, "tb_l": None
    }


def test_unknown_token_skipped():
    # 'Played and unfinished' 등 알 수 없는 토큰은 건너뛰고 세트만 수집
    outcome, sets = parse_score("6-4 ??? 6-3")
    assert outcome == "completed"
    assert [s["set_no"] for s in sets] == [1, 2]
    assert sets[1]["w_games"] == 6 and sets[1]["l_games"] == 3


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
