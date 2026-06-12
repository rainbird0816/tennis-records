import { useQuery } from "@tanstack/react-query";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { Champion, Tour } from "../api/types";
import { fmtDateRange } from "../lib/format";
import SeriesRecords from "../components/SeriesRecords";

/** /series/:slug — 시리즈 역대 우승자 (§9.2). */
export default function Series() {
  const { slug = "" } = useParams();
  const [params] = useSearchParams();
  const tour = (params.get("tour") as Tour) ?? "atp";

  const { data, isLoading, error } = useQuery({
    queryKey: ["series", slug, tour],
    queryFn: () => api<{ champions: Champion[] }>(`/series/${encodeURIComponent(slug)}/champions`, { tour }),
  });

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link to={`/category/GS`} className="text-sm text-neutral-400 hover:underline">
          ← 카테고리
        </Link>
        <h1 className="text-2xl font-bold">{slug}</h1>
        <span className="text-xs rounded bg-court text-white px-2 py-0.5">{tour.toUpperCase()}</span>
      </div>

      <SeriesRecords slug={slug} tour={tour} />

      <h2 className="text-sm font-semibold text-neutral-500 mb-3">🏆 역대 우승자</h2>

      {isLoading && <p className="text-neutral-400">불러오는 중…</p>}
      {error && <p className="text-amber-700 text-sm">데이터를 불러올 수 없습니다.</p>}

      <div className="rounded-lg border bg-white overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-neutral-100 text-neutral-500 text-xs">
            <tr>
              <th className="text-left px-4 py-2 w-16">연도</th>
              <th className="text-left px-4 py-2">우승</th>
              <th className="text-left px-4 py-2">준우승</th>
              <th className="text-left px-4 py-2">스코어</th>
              <th className="px-4 py-2 w-20"></th>
            </tr>
          </thead>
          <tbody>
            {data?.champions.map((c) => (
              <tr key={`${c.season}-${c.tourney_id}`} className="border-t hover:bg-neutral-50">
                <td className="px-4 py-2">
                  <div className="tabular-nums font-medium">{c.season}</div>
                  {fmtDateRange(c.start_date, c.tier, c.draw_size) && (
                    <div className="text-[0.65rem] text-neutral-400 tabular-nums whitespace-nowrap">
                      {fmtDateRange(c.start_date, c.tier, c.draw_size)}
                    </div>
                  )}
                </td>
                <td className="px-4 py-2">
                  <Link to={`/player/${tour}/${c.champion_id}`} className="font-medium text-court hover:underline">
                    {c.champion_name ?? `#${c.champion_id}`}
                  </Link>
                </td>
                <td className="px-4 py-2 text-neutral-600">
                  <Link to={`/player/${tour}/${c.runnerup_id}`} className="hover:underline">
                    {c.runnerup_name ?? `#${c.runnerup_id}`}
                  </Link>
                </td>
                <td className="px-4 py-2 font-mono text-xs text-neutral-500">{c.score}</td>
                <td className="px-4 py-2 text-right">
                  <Link
                    to={`/series/${encodeURIComponent(slug)}/${c.season}?tour=${tour}&tid=${encodeURIComponent(c.tourney_id)}`}
                    className="text-xs text-court hover:underline"
                  >
                    대진 →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
