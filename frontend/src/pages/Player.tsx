import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { PlayerProfile, Title, Tour } from "../api/types";
import { flagEmoji } from "../lib/flags";

const TIER_LABEL: Record<string, string> = {
  GS: "그랜드슬램", "1000": "Masters 1000", FINALS: "Tour Finals",
  "500": "500 시리즈", "250": "250 시리즈", OLYMPICS: "올림픽",
};

function StatBox({ label, value, suffix = "%" }: { label: string; value: number | null; suffix?: string }) {
  return (
    <div className="rounded-lg border bg-white px-3 py-2 text-center">
      <div className="text-lg font-bold text-court tabular-nums">
        {value == null ? "—" : `${value}${suffix}`}
      </div>
      <div className="text-[0.65rem] text-neutral-500 mt-0.5">{label}</div>
    </div>
  );
}

export default function Player() {
  const { tour = "atp", playerId = "" } = useParams();
  const t = tour as Tour;

  const { data, isLoading, error } = useQuery({
    queryKey: ["player", t, playerId],
    queryFn: () => api<PlayerProfile>(`/players/${t}/${playerId}`),
  });
  const titlesQ = useQuery({
    queryKey: ["player-titles", t, playerId],
    queryFn: () => api<{ titles: Title[] }>(`/players/${t}/${playerId}/titles`),
  });

  if (isLoading) return <p className="text-neutral-400">불러오는 중…</p>;
  if (error || !data) return <p className="text-amber-700 text-sm">선수를 찾을 수 없습니다.</p>;

  const p = data.player;
  const wins = data.record.wins ?? 0;
  const losses = data.record.losses ?? 0;
  const winPct = wins + losses ? ((wins / (wins + losses)) * 100).toFixed(1) : "—";
  const flag = flagEmoji(p.ioc);

  // 우승 목록을 tier 별로 그룹
  const titlesByTier = new Map<string, Title[]>();
  for (const tt of titlesQ.data?.titles ?? []) {
    if (!titlesByTier.has(tt.tier)) titlesByTier.set(tt.tier, []);
    titlesByTier.get(tt.tier)!.push(tt);
  }
  const tierOrder = ["GS", "1000", "FINALS", "500", "250", "OLYMPICS"];

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <header className="flex items-start gap-4 flex-wrap">
        <div className="text-5xl leading-none">{flag || "🎾"}</div>
        <div>
          <h1 className="text-3xl font-bold">{p.full_name}</h1>
          <div className="text-sm text-neutral-500 mt-1 flex gap-3 flex-wrap">
            <span className="rounded bg-court text-white px-2 py-0.5 text-xs">{t.toUpperCase()}</span>
            {p.ioc && <span>{p.ioc}</span>}
            {p.hand && <span>{p.hand === "R" ? "오른손잡이" : p.hand === "L" ? "왼손잡이" : p.hand}</span>}
            {p.height_cm && <span>{p.height_cm}cm</span>}
            {p.dob && <span>{String(p.dob).slice(0, 4)}년생</span>}
          </div>
          <div className="mt-2 text-sm">
            <span className="text-neutral-400">통산 </span>
            <span className="font-bold">{wins}승 {losses}패</span>
            <span className="text-neutral-400"> · 승률 </span>
            <span className="font-bold text-court">{winPct}%</span>
          </div>
        </div>
      </header>

      {/* 개관 / 플레이스타일 */}
      {data.style && (
        <section>
          <h2 className="text-sm font-semibold mb-2">개관 · 플레이스타일</h2>
          {data.style.labels.length > 0 && (
            <div className="flex gap-2 flex-wrap mb-3">
              {data.style.labels.map((l) => (
                <span key={l} className="rounded-full bg-court/10 text-court text-xs font-medium px-3 py-1">
                  {l}
                </span>
              ))}
            </div>
          )}
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
            <StatBox label="에이스율" value={data.style.ace_pct} />
            <StatBox label="더블폴트율" value={data.style.df_pct} />
            <StatBox label="1st 인率" value={data.style.first_in_pct} />
            <StatBox label="1st 득점" value={data.style.first_win_pct} />
            <StatBox label="2nd 득점" value={data.style.second_win_pct} />
            <StatBox label="BP 세이브" value={data.style.bp_saved_pct} />
          </div>
          <p className="text-[0.7rem] text-neutral-400 mt-1">
            서브 스탯 보유 경기 {data.style.matches.toLocaleString()}개 기준 (1991+).
          </p>
        </section>
      )}

      {/* 서피스별 승률 */}
      {data.by_surface.length > 0 && (
        <section>
          <h2 className="text-sm font-semibold mb-2">서피스별 승률</h2>
          <div className="space-y-1.5 max-w-lg">
            {data.by_surface.map((s) => (
              <div key={s.surface} className="flex items-center gap-3 text-sm">
                <span className="w-14 text-neutral-600">{s.surface}</span>
                <div className="flex-1 h-3 rounded bg-neutral-200 overflow-hidden">
                  <div className="h-full bg-court" style={{ width: `${s.pct ?? 0}%` }} />
                </div>
                <span className="w-28 text-right tabular-nums text-neutral-500">
                  {s.wins}–{s.losses} <span className="text-court font-medium">({s.pct}%)</span>
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* tier별 커리어 성적 */}
      <section>
        <h2 className="text-sm font-semibold mb-2">커리어 성적 (등급별)</h2>
        <div className="rounded-lg border bg-white overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-neutral-100 text-xs text-neutral-500">
              <tr>
                <th className="text-left px-4 py-2">등급</th>
                <th className="text-right px-4 py-2">우승</th>
                <th className="text-right px-4 py-2">준우승</th>
                <th className="text-right px-4 py-2">결승</th>
                <th className="text-right px-4 py-2">4강탈락</th>
              </tr>
            </thead>
            <tbody>
              {data.by_tier.map((c) => (
                <tr key={c.tier} className="border-t">
                  <td className="px-4 py-2 font-medium">{TIER_LABEL[c.tier] ?? c.tier}</td>
                  <td className="px-4 py-2 text-right font-bold text-court tabular-nums">{c.titles}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-neutral-500">{c.runner_ups}</td>
                  <td className="px-4 py-2 text-right tabular-nums">{c.finals}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-neutral-400">{c.sf_exits}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {t === "wta" && (
          <p className="text-[0.7rem] text-neutral-400 mt-1">WTA 1000/500/250 타이틀은 2021년 이후만 집계됩니다.</p>
        )}
      </section>

      {/* 우승 목록 (tier별 그룹) */}
      <section>
        <h2 className="text-sm font-semibold mb-2">우승 목록 ({titlesQ.data?.titles.length ?? 0})</h2>
        {tierOrder.filter((tier) => titlesByTier.has(tier)).map((tier) => (
          <div key={tier} className="mb-4">
            <h3 className="text-xs font-semibold text-neutral-500 mb-1">{TIER_LABEL[tier] ?? tier}</h3>
            <div className="flex flex-wrap gap-1.5">
              {titlesByTier.get(tier)!.map((tt, i) => (
                <span key={i} className="rounded border bg-white px-2 py-1 text-xs">
                  <span className="tabular-nums text-neutral-400 mr-1">{tt.season}</span>
                  {tt.name}
                </span>
              ))}
            </div>
          </div>
        ))}
        {titlesQ.data && titlesQ.data.titles.length === 0 && (
          <p className="text-neutral-500 text-sm">집계된 우승이 없습니다.</p>
        )}
      </section>
    </div>
  );
}
