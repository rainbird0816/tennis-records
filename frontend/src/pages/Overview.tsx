import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { SeriesOverview, Tour } from "../api/types";
import Flag from "../components/Flag";
import TourToggle from "../components/TourToggle";

const TITLES: Record<string, string> = {
  GS: "Grand Slam",
  "1000": "Masters 1000",
  "500": "ATP/WTA 500",
  "250": "ATP/WTA 250",
  FINALS: "Tour Finals",
};

/** /overview/:tier — 시리즈 통합 우승자 매트릭스 (가로=대회, 세로=연도). */
export default function Overview() {
  const { tier = "GS" } = useParams();
  const [tour, setTour] = useState<Tour>("atp");

  const { data, isLoading, error } = useQuery({
    queryKey: ["overview", tier, tour],
    queryFn: () => api<SeriesOverview>(`/overview/${tier}`, { tour }),
  });

  return (
    <div>
      <div className="flex items-center gap-3 mb-1 flex-wrap">
        <Link to={`/category/${tier}`} className="text-sm text-neutral-400 hover:underline">
          ← 카테고리
        </Link>
        <h1 className="text-2xl font-bold">{TITLES[tier] ?? tier} 역대 우승자</h1>
        <div className="ml-auto">
          <TourToggle value={tour} onChange={setTour} />
        </div>
      </div>
      <p className="text-xs text-neutral-500 mb-5">연도 × 대회 한눈에 보기 · 국기 + 우승 선수</p>

      {isLoading && <p className="text-neutral-400">불러오는 중…</p>}
      {error && <p className="text-amber-700 text-sm">데이터를 불러올 수 없습니다.</p>}

      {data && data.columns.length > 0 && (
        <div className="rounded-lg border bg-white overflow-x-auto">
          <table className="text-sm border-collapse">
            <thead className="bg-neutral-100 text-neutral-500 text-xs">
              <tr>
                <th className="sticky left-0 bg-neutral-100 text-left px-3 py-2 w-14 z-10">연도</th>
                {data.columns.map((c) => (
                  <th key={c} className="text-left px-3 py-2 whitespace-nowrap min-w-[150px]">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.seasons.map((yr) => (
                <tr key={yr} className="border-t hover:bg-neutral-50">
                  <th className="sticky left-0 bg-white text-left px-3 py-1.5 tabular-nums font-medium z-10">
                    {yr}
                  </th>
                  {data.columns.map((col) => {
                    const cell = data.grid[`${yr}|${col}`];
                    return (
                      <td key={col} className="px-3 py-1.5 whitespace-nowrap">
                        {cell ? (
                          <Link
                            to={`/player/${tour}/${cell.champion_id}`}
                            className="inline-flex items-center gap-1.5 hover:text-court hover:underline"
                          >
                            <Flag ioc={cell.ioc} />
                            <span>{cell.champion_name ?? `#${cell.champion_id}`}</span>
                          </Link>
                        ) : (
                          <span className="text-neutral-300">—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && data.columns.length === 0 && (
        <p className="text-neutral-500 text-sm">{tour.toUpperCase()} 데이터가 없습니다.</p>
      )}
    </div>
  );
}
