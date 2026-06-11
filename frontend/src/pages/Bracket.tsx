import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { MatchRow, TournamentDetail, Tour } from "../api/types";
import PlayerLabel from "../components/PlayerLabel";

const ROUND_LABEL: Record<string, string> = {
  RR: "라운드 로빈", R128: "128강", R64: "64강", R32: "32강", R16: "16강",
  QF: "8강", SF: "4강", BR: "동메달", F: "결승",
};

const PER_MATCH = 56; // 매치 카드 슬롯 높이(px)
const STUB = 16;      // 커넥터 가로 선 길이(px)

/** 한 경기 카드 — 승자 강조, 국기 + IOC + 이름. */
function MatchCard({ m }: { m: MatchRow }) {
  return (
    <Link
      to={`/match/${m.match_id}`}
      className="block rounded-md border bg-white shadow-sm hover:shadow-md hover:border-court transition overflow-hidden text-xs"
    >
      <div className="flex items-center justify-between px-2 py-1 border-l-2 border-court bg-court/5">
        <PlayerLabel name={m.winner_name} ioc={m.winner_ioc} id={m.winner_id} seed={m.winner_seed} className="font-semibold text-neutral-800 max-w-[150px]" />
        <span className="font-mono text-[0.7rem] text-court font-semibold shrink-0 ml-1">승</span>
      </div>
      <div className="flex items-center justify-between px-2 py-1 border-l-2 border-transparent text-neutral-500">
        <PlayerLabel name={m.loser_name} ioc={m.loser_ioc} id={m.loser_id} seed={m.loser_seed} className="max-w-[150px]" />
        {m.outcome !== "completed" && (
          <span className="text-[0.6rem] rounded bg-amber-100 text-amber-700 px-1 shrink-0 ml-1">
            {m.outcome === "RET" ? "기권" : m.outcome === "W/O" ? "부전승" : "실격"}
          </span>
        )}
      </div>
      <div className="px-2 py-0.5 font-mono text-[0.65rem] text-neutral-400 border-t bg-neutral-50">
        {m.score || "—"}
      </div>
    </Link>
  );
}

export default function Bracket() {
  const { slug = "", season = "" } = useParams();
  const [params] = useSearchParams();
  const tour = (params.get("tour") as Tour) ?? "atp";
  const tid = params.get("tid") ?? "";

  const { data, isLoading, error } = useQuery({
    queryKey: ["tournament", tour, tid],
    queryFn: () => api<TournamentDetail>(`/tournaments/${tour}/${encodeURIComponent(tid)}`),
    enabled: !!tid,
  });

  // round_order 로 그룹핑
  const byRound = new Map<number, { round: string; matches: MatchRow[] }>();
  for (const m of data?.matches ?? []) {
    if (!byRound.has(m.round_order)) byRound.set(m.round_order, { round: m.round, matches: [] });
    byRound.get(m.round_order)!.matches.push(m);
  }
  const ordered = [...byRound.entries()].sort((a, b) => a[0] - b[0]);
  const rr = ordered.filter(([, c]) => c.round === "RR");
  const elim = ordered.filter(([, c]) => c.round !== "RR");

  // 초반 라운드 접기: 기본은 16강(≤8경기)부터, 토글로 전체 펼침
  const [showAll, setShowAll] = useState(false);
  const collapsible = elim.some(([, c]) => c.matches.length > 8);
  const visibleElim = showAll || !collapsible
    ? elim
    : elim.filter(([, c]) => c.matches.length <= 8);

  // 토너먼트 트리: justify-around 가 풀 이진트리에서 정확히 중앙정렬됨
  const firstCount = visibleElim.length ? visibleElim[0][1].matches.length : 0;
  const treeHeight = firstCount * PER_MATCH;

  return (
    <div>
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <Link to={`/series/${encodeURIComponent(slug)}?tour=${tour}`} className="text-sm text-neutral-400 hover:underline">
          ← {slug}
        </Link>
        <h1 className="text-2xl font-bold">{slug} {season}</h1>
        {data?.tournament.surface && (
          <span className="text-xs rounded bg-neutral-200 px-2 py-0.5">{data.tournament.surface}</span>
        )}
        {data?.tournament.draw_size && (
          <span className="text-xs text-neutral-400">드로 {data.tournament.draw_size}</span>
        )}
        {collapsible && (
          <button
            onClick={() => setShowAll((v) => !v)}
            className="ml-auto text-xs rounded-lg border px-3 py-1.5 font-medium hover:bg-neutral-100"
          >
            {showAll ? "초반 라운드 접기" : "초반 라운드 펼치기"}
          </button>
        )}
      </div>

      {isLoading && <p className="text-neutral-400">불러오는 중…</p>}
      {error && <p className="text-amber-700 text-sm">대진을 불러올 수 없습니다.</p>}
      {!tid && <p className="text-amber-700 text-sm">tourney_id 가 없습니다. 시리즈 페이지에서 진입하세요.</p>}

      {/* 라운드 로빈 (파이널스 등) */}
      {rr.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xs font-semibold text-neutral-500 mb-2">{ROUND_LABEL.RR}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {rr[0][1].matches.map((m) => <MatchCard key={m.match_id} m={m} />)}
          </div>
        </section>
      )}

      {/* 단판 토너먼트 트리 */}
      {elim.length > 0 && (
        <div className="overflow-x-auto pb-4">
          <div className="flex gap-8 pt-7" style={{ minHeight: treeHeight }}>
            {visibleElim.map(([order, col], colIdx) => {
              const count = col.matches.length;
              const slot = treeHeight / Math.max(count, 1);
              const half = slot / 2;
              const isLast = colIdx === visibleElim.length - 1;
              const isFirst = colIdx === 0;
              return (
                <div
                  key={order}
                  className="relative flex flex-col justify-around shrink-0"
                  style={{ width: 210, height: treeHeight }}
                >
                  <div className="absolute -top-7 left-0 right-0 text-center text-xs font-semibold text-neutral-500">
                    {ROUND_LABEL[col.round] ?? col.round}
                  </div>
                  {col.matches.map((m, i) => (
                    <div key={m.match_id} className="relative">
                      <MatchCard m={m} />
                      {/* 들어오는 가로 스텁 (왼쪽) */}
                      {!isFirst && (
                        <span
                          className="absolute top-1/2 bg-neutral-300"
                          style={{ right: "100%", width: STUB, height: 1, marginRight: STUB }}
                        />
                      )}
                      {/* 나가는 가로 스텁 (오른쪽) + 짝을 잇는 세로선 */}
                      {!isLast && (
                        <>
                          <span
                            className="absolute top-1/2 bg-neutral-300"
                            style={{ left: "100%", width: STUB, height: 1 }}
                          />
                          <span
                            className="absolute bg-neutral-300"
                            style={{
                              left: `calc(100% + ${STUB}px)`,
                              width: 1,
                              height: half,
                              top: i % 2 === 0 ? "50%" : undefined,
                              bottom: i % 2 === 0 ? undefined : "50%",
                            }}
                          />
                        </>
                      )}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
