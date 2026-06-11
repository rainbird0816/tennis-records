import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { RecordLeader, Tour } from "../api/types";
import TourToggle from "../components/TourToggle";

const TITLES: Record<string, string> = {
  GS: "Grand Slam", "1000": "Masters 1000", "500": "500", "250": "250",
  FINALS: "Tour Finals", OLYMPICS: "Olympics",
};

/** /records/:tier — tier별 통산 우승/결승 랭킹 (§7). */
export default function Records() {
  const { tier = "GS" } = useParams();
  const [tour, setTour] = useState<Tour>("atp");
  const [metric, setMetric] = useState<"titles" | "finals">("titles");

  const { data, isLoading } = useQuery({
    queryKey: ["records", tier, tour, metric],
    queryFn: () => api<{ leaders: RecordLeader[] }>("/records", { tier, tour, metric }),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <h1 className="text-2xl font-bold">{TITLES[tier] ?? tier} 기록</h1>
        <div className="flex gap-3">
          <div className="inline-flex rounded-lg border overflow-hidden text-sm">
            {(["titles", "finals"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMetric(m)}
                className={`px-3 py-1.5 font-medium ${metric === m ? "bg-court text-white" : "bg-white text-neutral-700"}`}
              >
                {m === "titles" ? "우승" : "결승 진출"}
              </button>
            ))}
          </div>
          <TourToggle value={tour} onChange={setTour} />
        </div>
      </div>

      {isLoading && <p className="text-neutral-400">불러오는 중…</p>}

      <ol className="rounded-lg border bg-white divide-y">
        {data?.leaders.map((r, i) => (
          <li key={r.player_id} className="flex items-center px-4 py-2 text-sm">
            <span className="w-8 text-neutral-400 tabular-nums">{i + 1}</span>
            <Link to={`/player/${tour}/${r.player_id}`} className="flex-1 font-medium hover:underline">
              {r.full_name ?? `#${r.player_id}`}
            </Link>
            <span className="tabular-nums font-bold text-court">{r.n}</span>
          </li>
        ))}
      </ol>
      {data && data.leaders.length === 0 && (
        <p className="text-neutral-500 text-sm">데이터가 없습니다.</p>
      )}
    </div>
  );
}
