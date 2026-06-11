import type { Outcome, SetScore } from "../api/types";

interface Props {
  sets: SetScore[];
  winnerName: string;
  loserName: string;
  outcome: Outcome;
}

/** 세트별 게임 스코어보드. 타이브레이크는 위첨자(예 7-6⁷⁻⁵). 전 경기(1968~) 표시. §8 */
export default function SetScoreboard({ sets, winnerName, loserName, outcome }: Props) {
  const badge =
    outcome === "RET" ? "기권" : outcome === "W/O" ? "부전승" : outcome === "DEF" ? "실격" : null;

  const Row = ({ name, side }: { name: string; side: "w" | "l" }) => (
    <tr className={side === "w" ? "font-semibold" : "text-neutral-500"}>
      <td className="pr-4 py-1 whitespace-nowrap">
        {side === "w" && <span className="text-court mr-1">●</span>}
        {name}
      </td>
      {sets.map((s) => {
        const games = side === "w" ? s.w_games : s.l_games;
        const tb = side === "w" ? s.tb_w : s.tb_l;
        const won = side === "w" ? s.w_games > s.l_games : s.l_games > s.w_games;
        return (
          <td key={s.set_no} className={`px-2 py-1 text-center tabular-nums ${won ? "text-court" : ""}`}>
            {games}
            {tb != null && <sup className="text-[0.6em]">{tb}</sup>}
          </td>
        );
      })}
    </tr>
  );

  return (
    <div className="rounded-lg border bg-white p-4">
      <table className="text-sm">
        <tbody>
          <Row name={winnerName} side="w" />
          <Row name={loserName} side="l" />
        </tbody>
      </table>
      {badge && (
        <span className="mt-2 inline-block rounded bg-amber-100 text-amber-800 text-xs px-2 py-0.5">
          {badge}
        </span>
      )}
    </div>
  );
}
