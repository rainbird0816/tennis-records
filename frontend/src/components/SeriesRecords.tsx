import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { SeriesRecords, Tour } from "../api/types";
import Flag from "./Flag";

/** 대회 개관 — 역대 기록 카드 묶음 (최다 우승·연속·최장 경기·최고령/최연소). */
export default function SeriesRecords({ slug, tour }: { slug: string; tour: Tour }) {
  const { data, isLoading } = useQuery({
    queryKey: ["series-records", slug, tour],
    queryFn: () => api<SeriesRecords>(`/series/${encodeURIComponent(slug)}/records`, { tour }),
  });

  if (isLoading) return <p className="text-neutral-400 text-sm mb-6">기록 불러오는 중…</p>;
  if (!data) return null;

  const { summary, most_titles, most_consecutive, oldest_champion, youngest_champion, longest_match } = data;

  return (
    <section className="mb-8">
      <h2 className="text-sm font-semibold text-neutral-500 mb-3">📋 대회 개관 · 역대 기록</h2>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Card title="개최 횟수">
          <div className="text-2xl font-bold text-court tabular-nums">{summary.editions}</div>
          <div className="text-xs text-neutral-500">
            {summary.first_season}–{summary.last_season}
            {summary.surfaces.length > 0 && <> · {summary.surfaces.join("/")}</>}
          </div>
        </Card>

        {most_consecutive && (
          <Card title="최다 연속 우승">
            <PlayerLine row={most_consecutive} tour={tour} />
            <div className="text-xs text-neutral-500 mt-0.5 tabular-nums">
              {most_consecutive.count}연패 ({most_consecutive.seasons[0]}–
              {most_consecutive.seasons[most_consecutive.seasons.length - 1]})
            </div>
          </Card>
        )}

        {youngest_champion && (
          <Card title="최연소 우승">
            <PlayerLine row={youngest_champion} tour={tour} />
            <div className="text-xs text-neutral-500 mt-0.5 tabular-nums">
              {youngest_champion.age_str} · {youngest_champion.season}
            </div>
          </Card>
        )}

        {oldest_champion && (
          <Card title="최고령 우승">
            <PlayerLine row={oldest_champion} tour={tour} />
            <div className="text-xs text-neutral-500 mt-0.5 tabular-nums">
              {oldest_champion.age_str} · {oldest_champion.season}
            </div>
          </Card>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mt-3">
        {/* 최다 우승 랭킹 */}
        <div className="rounded-xl border bg-white p-4">
          <div className="text-xs font-semibold text-neutral-500 mb-2">최다 우승</div>
          <ol className="space-y-1">
            {most_titles.map((r, i) => (
              <li key={r.player_id} className="flex items-center gap-2 text-sm">
                <span className="w-4 text-neutral-400 tabular-nums">{i + 1}</span>
                <PlayerLine row={r} tour={tour} inline />
                <span className="ml-auto font-bold text-court tabular-nums">{r.count}회</span>
              </li>
            ))}
          </ol>
        </div>

        {/* 최장 시간 경기 */}
        {longest_match && (
          <div className="rounded-xl border bg-white p-4">
            <div className="text-xs font-semibold text-neutral-500 mb-2">최장 시간 경기</div>
            <Link to={`/match/${longest_match.match_id}`} className="block hover:bg-neutral-50 -m-1 p-1 rounded">
              <div className="text-2xl font-bold text-court tabular-nums">
                {Math.floor(longest_match.minutes / 60)}시간 {longest_match.minutes % 60}분
              </div>
              <div className="text-sm mt-1 flex items-center gap-1.5 flex-wrap">
                <Flag ioc={longest_match.winner_ioc} />
                <span className="font-medium">{longest_match.winner_name}</span>
                <span className="text-neutral-400">def.</span>
                <Flag ioc={longest_match.loser_ioc} />
                <span>{longest_match.loser_name}</span>
              </div>
              <div className="text-xs text-neutral-500 mt-0.5 tabular-nums">
                {longest_match.season} · {longest_match.round} · {longest_match.score}
              </div>
            </Link>
          </div>
        )}
      </div>
    </section>
  );
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-xl border bg-white p-4">
      <div className="text-xs font-semibold text-neutral-500 mb-1">{title}</div>
      {children}
    </div>
  );
}

function PlayerLine({
  row,
  tour,
  inline,
}: {
  row: { player_id: number; name: string | null; ioc: string | null };
  tour: Tour;
  inline?: boolean;
}) {
  const body = (
    <span className={`inline-flex items-center gap-1.5 ${inline ? "" : "font-semibold"}`}>
      <Flag ioc={row.ioc} />
      <span className="truncate">{row.name ?? `#${row.player_id}`}</span>
    </span>
  );
  return (
    <Link to={`/player/${tour}/${row.player_id}`} className="text-court hover:underline">
      {body}
    </Link>
  );
}
