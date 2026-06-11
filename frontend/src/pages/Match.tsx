import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { MatchDetail } from "../api/types";
import SetScoreboard from "../components/SetScoreboard";
import StatCompareBar from "../components/StatCompareBar";
import Flag from "../components/Flag";
import { fmtDate, nameWithIoc, seedSuffix } from "../lib/format";

/** /match/:matchId — Tier 1 매치 디테일 (§8). */
export default function Match() {
  const { matchId } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["match", matchId],
    queryFn: () => api<MatchDetail>(`/matches/${matchId}`),
    enabled: !!matchId,
  });

  if (isLoading) return <p className="text-neutral-400">불러오는 중…</p>;
  if (error || !data) return <p className="text-amber-700 text-sm">경기를 찾을 수 없습니다.</p>;

  // 스코어보드 텍스트(국기는 헤더에서 이미지로 표기)
  const wName = nameWithIoc(data.winner_name, data.winner_ioc, data.winner_id) + seedSuffix(data.winner_seed);
  const lName = nameWithIoc(data.loser_name, data.loser_ioc, data.loser_id) + seedSuffix(data.loser_seed);
  const date = fmtDate(data.start_date);

  return (
    <div className="space-y-6 max-w-2xl">
      <header>
        <div className="text-xs text-neutral-500">
          {data.tour.toUpperCase()} · {data.tournament_name} {data.season} · {data.round}
          {data.surface && ` · ${data.surface}`}
          {date && ` · ${date}`}
          {data.minutes != null && ` · ${data.minutes}분`}
        </div>
        <h1 className="text-xl font-bold mt-1 flex items-center gap-2 flex-wrap">
          <Link to={`/player/${data.tour}/${data.winner_id}`} className="inline-flex items-center gap-1.5 hover:underline">
            <Flag ioc={data.winner_ioc} /> {wName}
          </Link>
          <span className="text-neutral-400 font-normal">def.</span>
          <Link to={`/player/${data.tour}/${data.loser_id}`} className="inline-flex items-center gap-1.5 text-neutral-600 hover:underline">
            <Flag ioc={data.loser_ioc} /> {lName}
          </Link>
        </h1>
        <div className="text-sm text-neutral-500 font-mono">{data.score}</div>
      </header>

      <SetScoreboard sets={data.sets} winnerName={wName} loserName={lName} outcome={data.outcome} />

      {data.has_stats && data.stats ? (
        <section className="rounded-lg border bg-white p-4">
          <h2 className="text-sm font-semibold mb-2">스탯 대조</h2>
          <StatCompareBar label="에이스" w={data.stats.ace?.w ?? null} l={data.stats.ace?.l ?? null} />
          <StatCompareBar label="더블폴트" w={data.stats.df?.w ?? null} l={data.stats.df?.l ?? null} />
          <StatCompareBar label="서비스 게임" w={data.stats.SvGms?.w ?? null} l={data.stats.SvGms?.l ?? null} />
          <StatCompareBar label="BP 세이브" w={data.stats.bpSaved?.w ?? null} l={data.stats.bpSaved?.l ?? null} />
          {/* Phase 1: 1st 서브% 등 파생 지표 계산 추가 */}
        </section>
      ) : (
        <span className="inline-block rounded bg-neutral-100 text-neutral-500 text-xs px-2 py-1">
          세부 통계 미제공 (스코어보드만)
        </span>
      )}
    </div>
  );
}
