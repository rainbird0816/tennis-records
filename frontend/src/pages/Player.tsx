import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { PlayerProfile, Title, Tour } from "../api/types";

/** /player/:tour/:playerId — 프로필 + 통산 + 우승목록 (§9.4). */
export default function Player() {
  const { tour = "atp", playerId = "" } = useParams();
  const t = tour as Tour;

  const profile = useQuery({
    queryKey: ["player", t, playerId],
    queryFn: () => api<PlayerProfile>(`/players/${t}/${playerId}`),
  });
  const titles = useQuery({
    queryKey: ["player-titles", t, playerId],
    queryFn: () => api<{ titles: Title[] }>(`/players/${t}/${playerId}/titles`),
  });

  if (profile.isLoading) return <p className="text-neutral-400">불러오는 중…</p>;
  if (profile.error || !profile.data) return <p className="text-amber-700 text-sm">선수를 찾을 수 없습니다.</p>;

  const p = profile.data.player;
  const rec = profile.data.record;
  const wins = rec.wins ?? 0;
  const losses = rec.losses ?? 0;
  const winPct = wins + losses ? ((wins / (wins + losses)) * 100).toFixed(1) : "—";

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">{p.full_name}</h1>
        <div className="text-sm text-neutral-500 mt-1 flex gap-3 flex-wrap">
          <span className="rounded bg-court text-white px-2 py-0.5 text-xs">{t.toUpperCase()}</span>
          {p.ioc && <span>국적 {p.ioc}</span>}
          {p.hand && <span>{p.hand === "R" ? "오른손" : p.hand === "L" ? "왼손" : p.hand}</span>}
          {p.height_cm && <span>{p.height_cm}cm</span>}
          {p.dob && <span>생년 {String(p.dob).slice(0, 4)}</span>}
        </div>
      </header>

      <div className="flex gap-6 text-sm">
        <div><span className="text-neutral-400">통산 </span><span className="font-bold">{wins}승 {losses}패</span></div>
        <div><span className="text-neutral-400">승률 </span><span className="font-bold text-court">{winPct}%</span></div>
      </div>

      <section>
        <h2 className="text-sm font-semibold mb-2">우승 목록 ({titles.data?.titles.length ?? 0})</h2>
        {titles.data && titles.data.titles.length > 0 ? (
          <div className="rounded-lg border bg-white divide-y text-sm">
            {titles.data.titles.map((tt, i) => (
              <div key={i} className="flex px-3 py-2 gap-3">
                <span className="tabular-nums text-neutral-400 w-12">{tt.season}</span>
                <span className="flex-1 font-medium">{tt.name}</span>
                <span className="text-xs rounded bg-neutral-100 px-2 py-0.5">{tt.tier}</span>
                <span className="font-mono text-xs text-neutral-400">{tt.score}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-neutral-500 text-sm">
            기록된 우승이 없습니다. <span className="text-neutral-400">(WTA 등급 타이틀은 2021+만 집계)</span>
          </p>
        )}
      </section>
    </div>
  );
}
