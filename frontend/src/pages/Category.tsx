import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { OlympicEdition, Series, Tour } from "../api/types";
import TourToggle from "../components/TourToggle";

const TITLES: Record<string, string> = {
  GS: "Grand Slam",
  "1000": "Masters 1000",
  "500": "ATP/WTA 500",
  "250": "ATP/WTA 250",
  FINALS: "Tour Finals",
  OLYMPICS: "Olympics",
};

/** 올림픽 — 개최 연도(에디션) 카드 → 메달 페이지. */
function OlympicsEditions() {
  const { data, isLoading } = useQuery({
    queryKey: ["olympics-editions"],
    queryFn: () => api<{ editions: OlympicEdition[] }>("/olympics/editions"),
  });
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">🏅 Olympics 단식</h1>
      {isLoading && <p className="text-neutral-400">불러오는 중…</p>}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {data?.editions.map((e) => (
          <Link
            key={e.season}
            to={`/olympics/${e.season}`}
            className="rounded-xl border bg-white p-4 hover:shadow-md transition text-center"
          >
            <div className="text-xl font-bold">{e.season}</div>
            <div className="text-xs text-neutral-500 mt-1">메달 보기</div>
          </Link>
        ))}
      </div>
    </div>
  );
}

/** /category/:tier — 시리즈 카드 + ATP/WTA 토글 (§9.2). 개최 시기순 정렬(백엔드). */
export default function Category() {
  const { tier = "GS" } = useParams();
  const [tour, setTour] = useState<Tour>("atp");

  const { data, isLoading, error } = useQuery({
    queryKey: ["category", tier, tour],
    queryFn: () => api<{ series: Series[] }>(`/categories/${tier}`, { tour }),
    enabled: tier !== "OLYMPICS",
  });

  if (tier === "OLYMPICS") return <OlympicsEditions />;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">{TITLES[tier] ?? tier}</h1>
        <TourToggle value={tour} onChange={setTour} />
      </div>

      {isLoading && <p className="text-neutral-400">불러오는 중…</p>}
      {error && <p className="text-amber-700 text-sm">데이터를 불러올 수 없습니다.</p>}
      {data && data.series.length === 0 && (
        <p className="text-neutral-500 text-sm">
          {tour.toUpperCase()} {TITLES[tier] ?? tier} 데이터가 없습니다.
        </p>
      )}

      {(() => {
        const active = data?.series.filter((s) => s.active) ?? [];
        const defunct = data?.series.filter((s) => !s.active) ?? [];
        return (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {active.map((s) => (
                <SeriesCard key={s.name} s={s} tour={tour} />
              ))}
            </div>

            {defunct.length > 0 && (
              <section className="mt-8">
                <h2 className="text-sm font-semibold text-neutral-500 mb-3 flex items-center gap-2">
                  <span className="h-px flex-1 bg-neutral-200" />
                  폐지된 대회 ({defunct.length})
                  <span className="h-px flex-1 bg-neutral-200" />
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {defunct.map((s) => (
                    <SeriesCard key={s.name} s={s} tour={tour} defunct />
                  ))}
                </div>
              </section>
            )}
          </>
        );
      })()}
    </div>
  );
}

function SeriesCard({ s, tour, defunct }: { s: Series; tour: Tour; defunct?: boolean }) {
  return (
    <Link
      to={`/series/${encodeURIComponent(s.name)}?tour=${tour}`}
      className={`rounded-xl border p-4 hover:shadow-md transition ${
        defunct ? "bg-neutral-50 opacity-80 hover:opacity-100" : "bg-white"
      }`}
    >
      <div className="flex items-center gap-2">
        <span className={`font-semibold ${defunct ? "text-neutral-600" : ""}`}>{s.name}</span>
        {defunct && (
          <span className="text-[0.65rem] rounded bg-neutral-200 text-neutral-600 px-1.5 py-0.5">폐지</span>
        )}
      </div>
      <div className="text-xs text-neutral-500 mt-0.5">
        {s.first_season}–{s.last_season} · {s.seasons}회 개최
      </div>
      {s.latest_champion && (
        <div className="mt-3 text-sm">
          <span className="text-neutral-400 text-xs">
            {defunct ? "마지막 우승" : `${s.latest_champion.season} 우승`}
          </span>
          <div className={`font-medium ${defunct ? "text-neutral-600" : "text-court"}`}>
            {s.latest_champion.champion_name ?? `#${s.latest_champion.champion_id}`}
            {defunct && <span className="text-neutral-400 text-xs ml-1">({s.latest_champion.season})</span>}
          </div>
        </div>
      )}
    </Link>
  );
}
