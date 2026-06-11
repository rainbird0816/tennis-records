import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { H2HBreakdown, H2HResult, PlayerHit, Tour } from "../api/types";
import SearchBar from "../components/SearchBar";
import TourToggle from "../components/TourToggle";

function BreakdownTable({ title, dimKey, rows }: { title: string; dimKey: "surface" | "tier" | "round"; rows: H2HBreakdown[] }) {
  if (!rows.length) return null;
  return (
    <div>
      <h3 className="text-xs font-semibold text-neutral-500 mb-1">{title}</h3>
      <div className="rounded-lg border bg-white divide-y text-sm">
        {rows.map((r) => (
          <div key={r[dimKey]} className="flex justify-between px-3 py-1.5">
            <span className="text-neutral-600">{r[dimKey]}</span>
            <span className="tabular-nums">
              <span className="text-court font-medium">{r.p1_wins}</span>
              <span className="text-neutral-300 mx-1">–</span>
              <span className="text-neutral-500 font-medium">{r.p2_wins}</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/** /h2h — 상대전적 + 서피스/라운드/tier 분해 (§9.4). */
export default function H2H() {
  const [tour, setTour] = useState<Tour>("atp");
  const [p1, setP1] = useState<PlayerHit | null>(null);
  const [p2, setP2] = useState<PlayerHit | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["h2h", tour, p1?.player_id, p2?.player_id],
    queryFn: () => api<H2HResult>("/h2h", { tour, p1: p1!.player_id, p2: p2!.player_id }),
    enabled: !!p1 && !!p2,
  });

  const total = data?.summary.total ?? 0;
  const p1pct = total ? (data!.summary.p1_wins / total) * 100 : 50;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">H2H 상대전적</h1>
        <TourToggle value={tour} onChange={(t) => { setTour(t); setP1(null); setP2(null); }} />
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <SearchBar tour={tour} placeholder="선수 1" onSelect={setP1} />
        <SearchBar tour={tour} placeholder="선수 2" onSelect={setP2} />
      </div>

      {(!p1 || !p2) && <p className="text-neutral-400 text-sm">두 선수를 선택하세요.</p>}
      {isLoading && <p className="text-neutral-400">불러오는 중…</p>}

      {data && (
        <div className="space-y-6">
          <div>
            <div className="flex justify-between text-lg font-bold mb-1">
              <span className="text-court">{data.p1_name} {data.summary.p1_wins}</span>
              <span className="text-neutral-500">{data.summary.p2_wins} {data.p2_name}</span>
            </div>
            <div className="flex h-3 rounded overflow-hidden bg-neutral-200">
              <div className="bg-court" style={{ width: `${p1pct}%` }} />
              <div className="bg-neutral-400" style={{ width: `${100 - p1pct}%` }} />
            </div>
            <div className="text-center text-xs text-neutral-400 mt-1">통산 {total}경기</div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <BreakdownTable title="서피스별" dimKey="surface" rows={data.by_surface} />
            <BreakdownTable title="tier별" dimKey="tier" rows={data.by_tier} />
            <BreakdownTable title="라운드별" dimKey="round" rows={data.by_round} />
          </div>

          <div>
            <h3 className="text-xs font-semibold text-neutral-500 mb-1">경기 목록</h3>
            <div className="rounded-lg border bg-white divide-y text-sm">
              {data.matches.map((m) => (
                <Link key={m.match_id} to={`/match/${m.match_id}`} className="flex justify-between px-3 py-2 hover:bg-neutral-50">
                  <span className="text-neutral-500 w-32 shrink-0">{m.season} {m.tournament_name}</span>
                  <span className="text-neutral-400 w-12 shrink-0">{m.round}</span>
                  <span className="flex-1">
                    <span className="text-court font-medium">{m.winner_name}</span> def. {m.loser_name}
                  </span>
                  <span className="font-mono text-xs text-neutral-400">{m.score}</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
