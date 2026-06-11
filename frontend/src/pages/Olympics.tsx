import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Medal } from "../api/types";
import Flag from "../components/Flag";

const MEDAL_META: Record<string, { label: string; emoji: string; cls: string }> = {
  gold: { label: "금", emoji: "🥇", cls: "bg-yellow-50 border-yellow-200" },
  silver: { label: "은", emoji: "🥈", cls: "bg-neutral-100 border-neutral-300" },
  bronze: { label: "동", emoji: "🥉", cls: "bg-orange-50 border-orange-200" },
};
const ORDER = ["gold", "silver", "bronze"];

function MedalColumn({ title, medals }: { title: string; medals: Medal[] }) {
  const tour = medals[0]?.tour ?? "atp";
  const byMedal = (m: string) => medals.find((x) => x.medal === m);
  return (
    <div>
      <h2 className="text-sm font-semibold mb-2">{title}</h2>
      <div className="space-y-2">
        {ORDER.map((m) => {
          const meta = MEDAL_META[m];
          const row = byMedal(m);
          return (
            <div key={m} className={`flex items-center gap-3 rounded-lg border px-3 py-2 ${meta.cls}`}>
              <span className="text-xl">{meta.emoji}</span>
              <span className="text-xs font-semibold text-neutral-500 w-4">{meta.label}</span>
              {row ? (
                <Link to={`/player/${tour}/${row.player_id}`} className="flex items-center gap-2 font-medium hover:underline">
                  <Flag ioc={row.ioc} />
                  {row.ioc && <span className="text-[0.65rem] text-neutral-400 font-semibold">{row.ioc}</span>}
                  {row.full_name ?? `#${row.player_id}`}
                </Link>
              ) : (
                <span className="text-neutral-400 text-sm">—</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/** /olympics/:season — 남·녀 메달 테이블 (§9.4, Phase 6). */
export default function Olympics() {
  const { season = "" } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["olympics", season],
    queryFn: () => api<{ season: number; atp: Medal[]; wta: Medal[] }>(`/olympics/${season}/medals`),
  });

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link to="/category/OLYMPICS" className="text-sm text-neutral-400 hover:underline">← 올림픽</Link>
        <h1 className="text-2xl font-bold">🏅 {season} 올림픽 단식 메달</h1>
      </div>

      {isLoading && <p className="text-neutral-400">불러오는 중…</p>}
      {error && <p className="text-amber-700 text-sm">메달 데이터를 불러올 수 없습니다.</p>}

      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 max-w-3xl">
          <MedalColumn title="남자 단식 (ATP)" medals={data.atp} />
          <MedalColumn title="여자 단식 (WTA)" medals={data.wta} />
        </div>
      )}
      {data && data.atp.length === 0 && data.wta.length === 0 && (
        <p className="text-neutral-500 text-sm">메달 데이터가 없습니다 (동메달 결정전이 없던 초기 대회 등).</p>
      )}
    </div>
  );
}
