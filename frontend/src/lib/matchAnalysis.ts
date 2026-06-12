import type { MatchDetail } from "../api/types";

/** 경기 데이터(세트·스탯·시간·랭킹)에서 규칙 기반 분석 코멘트를 생성.
 *  외부 LLM/API 없이 보유 데이터만으로 도출(프로젝트 원칙 §0). */
export function matchAnalysis(d: MatchDetail): string[] {
  const out: string[] = [];
  const w = d.winner_name ?? "승자";
  const l = d.loser_name ?? "패자";
  const sets = d.sets ?? [];
  const n = sets.length;

  // 0) 결과 유형 (기권/부전승/실격)
  if (d.outcome === "W/O") return [`${l} 선수의 기권(부전승)으로 ${w} 선수가 진출했습니다.`];
  if (d.outcome === "DEF") out.push(`${l} 선수의 실격으로 종료된 경기입니다.`);
  if (d.outcome === "RET") out.push(`${l} 선수가 경기 도중 기권했습니다.`);

  const lostByWinner = sets.filter((s) => s.w_games < s.l_games).length;
  const straight = n > 0 && lostByWinner === 0;
  const bo = d.best_of ?? (n > 3 ? 5 : 3);

  // 1) 세트 양상
  if (straight && d.outcome === "completed") {
    out.push(
      bo === 5 && n >= 3
        ? `${w} 선수가 세트를 하나도 내주지 않고 스트레이트 세트(${n}-0)로 완승했습니다.`
        : `${w} 선수가 ${n}-0 완승을 거뒀습니다.`,
    );
  } else if (bo === 5 && n === 5) {
    out.push(`풀세트(5세트)까지 가는 혈투 끝에 ${w} 선수가 승리했습니다.`);
  } else if (bo === 3 && n === 3 && d.outcome === "completed") {
    out.push(`3세트 접전 끝에 ${w} 선수가 승부를 가져갔습니다.`);
  }

  // 2) 역전승
  if (n >= 2 && sets[0].w_games < sets[0].l_games) {
    out.push(
      lostByWinner >= 2
        ? `${w} 선수가 ${lostByWinner}세트를 먼저 내주고도 뒤집은 대역전승입니다.`
        : `${w} 선수가 첫 세트를 내준 뒤 흐름을 바꿔 역전승했습니다.`,
    );
  }

  // 3) 타이브레이크
  const tb = sets.filter((s) => s.tb_w != null || s.tb_l != null).length;
  if (tb >= 2) out.push(`타이브레이크만 ${tb}차례 벌어진 초접전이었습니다.`);
  else if (tb === 1) out.push(`타이브레이크 승부가 분수령이 됐습니다.`);

  // 4) 베이글(6-0) 세트
  if (sets.some((s) => s.w_games > s.l_games && s.l_games === 0)) {
    out.push(`상대에게 한 게임도 허용하지 않은 '베이글(6-0)' 세트가 나왔습니다.`);
  }

  // 5) 경기 시간
  if (d.minutes != null) {
    if (d.minutes >= 240) {
      out.push(`${Math.floor(d.minutes / 60)}시간 ${d.minutes % 60}분에 이르는 장기전이었습니다.`);
    } else if (d.minutes <= 70 && straight && d.outcome === "completed") {
      out.push(`단 ${d.minutes}분 만에 끝난 속전속결 경기입니다.`);
    }
  }

  // 6) 랭킹 이변(업셋)
  if (d.winner_rank && d.loser_rank && d.winner_rank > d.loser_rank + 10) {
    out.push(
      `랭킹 ${d.winner_rank}위 ${w} 선수가 상위 랭커(${d.loser_rank}위) ${l} 선수를 꺾는 이변을 연출했습니다.`,
    );
  }

  // 7) 스탯 기반 (1991+ 보유 경기)
  if (d.has_stats && d.stats) {
    const wAce = d.stats.ace?.w;
    if (wAce != null && wAce >= 20) {
      out.push(`${w} 선수가 에이스 ${wAce}개를 터뜨리며 서브로 압도했습니다.`);
    }
    const faced = d.stats.bpFaced?.w;
    const saved = d.stats.bpSaved?.w;
    if (faced != null && saved != null && faced >= 6 && saved / faced >= 0.7) {
      out.push(`${w} 선수가 서브 게임에서 브레이크포인트 ${faced}개 중 ${saved}개를 막아내며 위기를 넘겼습니다.`);
    }
  }

  // 폴백: 도출된 코멘트가 없으면 기본 요약
  if (out.length === 0 && d.score) {
    out.push(`${w} 선수가 ${d.score} 스코어로 ${l} 선수를 꺾었습니다.`);
  }

  return out.slice(0, 5);
}
