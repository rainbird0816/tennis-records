import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { GrandSlamTimeline, Tour } from "../api/types";

/** 대회명 → 짧은 칼럼 라벨. */
const SLAM_ABBR: Record<string, string> = {
  "Australian Open": "호주",
  "Roland Garros": "롤랑가로",
  Wimbledon: "윔블던",
  "US Open": "US오픈",
};

/** 셀 코드 → 표시 라벨 (F 는 Runner-up 으로). */
const CODE_LABEL: Record<string, string> = { F: "Runner-up" };

/** 셀 코드 → 색상 클래스 — 트로피 톤(우승 골드 / 준우승 실버 / 4강 브론즈). */
function cellClass(code: string): string {
  switch (code) {
    case "W":
      return "bg-yellow-300 text-yellow-900 font-bold"; // 골드
    case "F":
      return "bg-slate-300 text-slate-700 font-semibold"; // 실버(준우승)
    case "SF":
      return "bg-orange-200 text-orange-900 font-medium"; // 브론즈
    case "QF":
      return "bg-orange-50 text-orange-700"; // 아주 연한 강조
    default:
      return "text-neutral-500"; // 4R/3R/2R/1R
  }
}

/** 선수 상세용 연도별 그랜드슬램 성적표 (GS 16강 이상 진출자만 표시). */
export default function GrandSlamTable({ tour, playerId }: { tour: Tour; playerId: string }) {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["player-grand-slams", tour, playerId],
    queryFn: () => api<GrandSlamTimeline>(`/players/${tour}/${playerId}/grand-slams`),
  });

  // API 연결 실패: 자격 여부를 알 수 없으므로 조용히 숨기지 않고 재시도 안내.
  if (isError) {
    return (
      <section>
        <h2 className="text-sm font-semibold mb-2">연도별 그랜드슬램</h2>
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 flex items-center gap-3">
          <span>기록을 불러오지 못했습니다. (API 연결 실패)</span>
          <button
            onClick={() => refetch()}
            className="rounded border border-amber-300 bg-white px-2 py-0.5 text-xs font-medium hover:bg-amber-100"
          >
            다시 시도
          </button>
        </div>
      </section>
    );
  }

  if (isLoading || !data?.available || !data.results || !data.slams) return null;

  const slams = data.slams;
  const years = Object.keys(data.results).sort((a, b) => Number(b) - Number(a));

  // 대회별 통산 우승 수 (열 푸터용)
  const titleCount: Record<string, number> = {};
  for (const yr of years) {
    for (const s of slams) {
      if (data.results[yr][s] === "W") titleCount[s] = (titleCount[s] ?? 0) + 1;
    }
  }
  const totalTitles = Object.values(titleCount).reduce((a, b) => a + b, 0);

  return (
    <section>
      <h2 className="text-sm font-semibold mb-2">
        연도별 그랜드슬램
        {totalTitles > 0 && <span className="text-court ml-2">우승 {totalTitles}회</span>}
      </h2>
      <div className="rounded-lg border bg-white overflow-x-auto">
        <table className="text-sm border-collapse w-full">
          <thead className="bg-neutral-100 text-neutral-500 text-xs">
            <tr>
              <th className="sticky left-0 bg-neutral-100 text-left px-3 py-2 w-14 z-10">연도</th>
              {slams.map((s) => (
                <th key={s} className="px-3 py-2 text-center whitespace-nowrap" title={s}>
                  {SLAM_ABBR[s] ?? s}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {years.map((yr) => (
              <tr key={yr} className="border-t">
                <th className="sticky left-0 bg-white text-left px-3 py-1 tabular-nums font-medium z-10">
                  {yr}
                </th>
                {slams.map((s) => {
                  const code = data.results![yr][s];
                  return (
                    <td key={s} className="px-1.5 py-1 text-center">
                      {code ? (
                        <span className={`inline-block min-w-[2.2rem] whitespace-nowrap rounded px-1.5 py-0.5 text-xs ${cellClass(code)}`}>
                          {CODE_LABEL[code] ?? code}
                        </span>
                      ) : (
                        <span className="text-neutral-200">·</span>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
          {totalTitles > 0 && (
            <tfoot className="border-t bg-neutral-50 text-xs">
              <tr>
                <th className="sticky left-0 bg-neutral-50 text-left px-3 py-1.5 text-neutral-500 z-10">
                  우승
                </th>
                {slams.map((s) => (
                  <td key={s} className="px-3 py-1.5 text-center tabular-nums font-semibold text-court">
                    {titleCount[s] ?? 0}
                  </td>
                ))}
              </tr>
            </tfoot>
          )}
        </table>
      </div>
      <p className="text-[0.7rem] text-neutral-400 mt-1">
        W 우승 · Runner-up 준우승 · SF 4강 · QF 8강 · 4R 16강 · 3R 32강 · 2R 64강 · 1R 1회전 (빈칸=불참)
      </p>
    </section>
  );
}
