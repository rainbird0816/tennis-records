import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { RankingPoint } from "../api/types";

/** 시즌별 연말/최고 랭킹 추이 (#1 이 위로 오도록 Y축 반전). */
export default function RankChart({ data }: { data: RankingPoint[] }) {
  if (!data.length) {
    return <p className="text-neutral-400 text-sm">랭킹 데이터가 없습니다.</p>;
  }

  // Y축 위쪽이 1위가 되도록 reversed. 도메인은 1 ~ 최저순위(여유).
  const ranks = data.flatMap((d) =>
    [d.year_end_rank, d.best_rank].filter((x): x is number => x != null),
  );
  const worst = Math.max(...ranks, 10);

  return (
    <div className="rounded-lg border bg-white p-3">
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="season" tick={{ fontSize: 11 }} />
          <YAxis
            reversed
            domain={[1, worst]}
            allowDecimals={false}
            tick={{ fontSize: 11 }}
            width={36}
            label={{ value: "순위", angle: -90, position: "insideLeft", style: { fontSize: 11, fill: "#888" } }}
          />
          <Tooltip
            formatter={(v: number, name: string) => [`${v}위`, name === "best_rank" ? "최고" : "연말"]}
            labelFormatter={(l) => `${l} 시즌`}
            contentStyle={{ fontSize: 12 }}
          />
          <Line type="monotone" dataKey="best_rank" stroke="#2e8b57" strokeWidth={1} dot={false} strokeDasharray="4 3" />
          <Line type="monotone" dataKey="year_end_rank" stroke="#1f6f43" strokeWidth={2} dot={{ r: 2 }} />
        </LineChart>
      </ResponsiveContainer>
      <div className="flex gap-4 justify-center text-[0.7rem] text-neutral-500 mt-1">
        <span><span className="inline-block w-3 border-t-2 border-court align-middle mr-1" />연말 순위</span>
        <span><span className="inline-block w-3 border-t border-dashed border-court-light align-middle mr-1" />시즌 최고</span>
      </div>
    </div>
  );
}
