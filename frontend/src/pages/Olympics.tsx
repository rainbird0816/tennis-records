import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Medal, Tour } from "../api/types";
import Flag from "../components/Flag";

const MEDAL_META: Record<string, { label: string; emoji: string; cls: string }> = {
  gold: { label: "금", emoji: "🥇", cls: "bg-yellow-50 border-yellow-200" },
  silver: { label: "은", emoji: "🥈", cls: "bg-neutral-100 border-neutral-300" },
  bronze: { label: "동", emoji: "🥉", cls: "bg-orange-50 border-orange-200" },
};
const ORDER = ["gold", "silver", "bronze"];

function MedalRow({ medal, rows, tour }: { medal: string; rows: Medal[]; tour: Tour }) {
  const meta = MEDAL_META[medal];
  return (
    <div className={`flex items-start gap-3 rounded-lg border px-3 py-2 ${meta.cls}`}>
      <span className="text-xl leading-tight">{meta.emoji}</span>
      <span className="text-xs font-semibold text-neutral-500 w-4 mt-1">{meta.label}</span>
      <div className="flex flex-col gap-1">
        {rows.length === 0 && <span className="text-neutral-400 text-sm">—</span>}
        {rows.map((r) => (
          <Link
            key={r.player_id}
            to={`/player/${tour}/${r.player_id}`}
            className="flex items-center gap-2 font-medium hover:underline"
          >
            <Flag ioc={r.ioc} />
            {r.ioc && <span className="text-[0.65rem] text-neutral-400 font-semibold">{r.ioc}</span>}
            {r.full_name ?? `#${r.player_id}`}
          </Link>
        ))}
      </div>
    </div>
  );
}

function MedalColumn({ title, medals, tid, season }: { title: string; medals: Medal[]; tid: string | null; season: string }) {
  const tour = medals[0]?.tour ?? "atp";
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold">{title}</h2>
        {tid && (
          <Link
            to={`/series/Olympics/${season}?tour=${tour}&tid=${encodeURIComponent(tid)}`}
            className="text-xs text-court hover:underline"
          >
            대진 보기 →
          </Link>
        )}
      </div>
      <div className="space-y-2">
        {ORDER.map((m) => (
          <MedalRow key={m} medal={m} tour={tour} rows={medals.filter((x) => x.medal === m)} />
        ))}
      </div>
    </div>
  );
}

/** /olympics/:season — 남·녀 메달 테이블 + 대진 링크 (§9.4, Phase 6). */
export default function Olympics() {
  const { season = "" } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["olympics", season],
    queryFn: () =>
      api<{ season: number; atp: Medal[]; wta: Medal[]; atp_tid: string | null; wta_tid: string | null }>(
        `/olympics/${season}/medals`,
      ),
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
          <MedalColumn title="남자 단식 (ATP)" medals={data.atp} tid={data.atp_tid} season={season} />
          <MedalColumn title="여자 단식 (WTA)" medals={data.wta} tid={data.wta_tid} season={season} />
        </div>
      )}
      {data && data.atp.length === 0 && data.wta.length === 0 && (
        <p className="text-neutral-500 text-sm">메달 데이터가 없습니다.</p>
      )}
      <p className="text-[0.7rem] text-neutral-400 mt-6">
        1988·1992년은 동메달 결정전이 없어 4강 탈락자 2명에게 공동 동메달이 수여되었습니다.
      </p>
    </div>
  );
}
