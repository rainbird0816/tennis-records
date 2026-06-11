import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { CategoryInfo } from "../api/types";

const TITLES: Record<string, string> = {
  GS: "Grand Slam",
  "1000": "Masters 1000",
  "500": "ATP/WTA 500",
  "250": "ATP/WTA 250",
  FINALS: "Tour Finals",
  OLYMPICS: "Olympics",
};

export default function Home() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["categories"],
    queryFn: () => api<{ categories: CategoryInfo[] }>("/categories"),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-1">역대 테니스 기록</h1>
      <p className="text-neutral-500 mb-6 text-sm">
        카테고리를 선택해 역대 우승자·대진·전적과 경기 상세를 확인하세요.
      </p>

      {isLoading && <p className="text-neutral-400">불러오는 중…</p>}
      {error && (
        <p className="text-amber-700 text-sm">
          API 연결 실패 — 백엔드(<code>uvicorn app.main:app</code>)와 ETL(
          <code>build_db</code>)을 먼저 실행하세요.
        </p>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {(data?.categories ?? Object.keys(TITLES).map((t) => ({ tier: t, availability: [] } as CategoryInfo))).map(
          (c) => (
            <Link
              key={c.tier}
              to={`/category/${c.tier}`}
              className="rounded-xl border bg-white p-4 hover:shadow-md transition"
            >
              <div className="font-semibold">{TITLES[c.tier] ?? c.tier}</div>
              <div className="mt-1 text-xs text-neutral-500">
                {c.availability.length
                  ? c.availability.map((a) => `${a.tour.toUpperCase()} ${a.min_season}–${a.max_season}`).join(" · ")
                  : "데이터 대기"}
              </div>
            </Link>
          ),
        )}
      </div>
    </div>
  );
}
