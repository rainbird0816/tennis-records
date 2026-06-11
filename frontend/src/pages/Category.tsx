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
