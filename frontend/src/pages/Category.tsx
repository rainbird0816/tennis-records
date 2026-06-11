import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Series, Tour } from "../api/types";
import TourToggle from "../components/TourToggle";

const TITLES: Record<string, string> = {
  GS: "Grand Slam",
  "1000": "Masters 1000",
  "500": "ATP/WTA 500",
  "250": "ATP/WTA 250",
  FINALS: "Tour Finals",
  OLYMPICS: "Olympics",
};

/** /category/:tier — 시리즈 카드 + ATP/WTA 토글 (§9.2). */
export default function Category() {
  const { tier = "GS" } = useParams();
  const [tour, setTour] = useState<Tour>("atp");

  const { data, isLoading, error } = useQuery({
    queryKey: ["category", tier, tour],
    queryFn: () => api<{ series: Series[] }>(`/categories/${tier}`, { tour }),
  });

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

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {data?.series.map((s) => (
          <Link
            key={s.name}
            to={`/series/${encodeURIComponent(s.name)}?tour=${tour}`}
            className="rounded-xl border bg-white p-4 hover:shadow-md transition"
          >
            <div className="font-semibold">{s.name}</div>
            <div className="text-xs text-neutral-500 mt-0.5">
              {s.first_season}–{s.last_season} · {s.seasons}회 개최
            </div>
            {s.latest_champion && (
              <div className="mt-3 text-sm">
                <span className="text-neutral-400 text-xs">{s.latest_champion.season} 우승</span>
                <div className="font-medium text-court">
                  {s.latest_champion.champion_name ?? `#${s.latest_champion.champion_id}`}
                </div>
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}
