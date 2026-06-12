/** "YYYYMMDD" → "YYYY.MM.DD" (대회 시작일). 잘못된 값은 빈 문자열. */
export function fmtDate(yyyymmdd: string | null | undefined): string {
  const s = String(yyyymmdd ?? "");
  if (s.length < 8) return "";
  return `${s.slice(0, 4)}.${s.slice(4, 6)}.${s.slice(6, 8)}`;
}

// 대회 기간(일) 추정 — 데이터엔 시작일만 있어 tier/드로 크기로 근사.
const TIER_DURATION: Record<string, number> = { GS: 14, FINALS: 8, OLYMPICS: 9 };

export function tourneyDurationDays(tier?: string | null, drawSize?: number | null): number {
  if (tier && TIER_DURATION[tier]) return TIER_DURATION[tier];
  if (tier === "1000") {
    const d = drawSize ?? 0;
    return d >= 96 ? 12 : d >= 56 ? 9 : 7;
  }
  return 7; // 500 / 250 / 기타
}

/** 대회 시작일 + tier/드로 → "YYYY.MM.DD – MM.DD" 기간 표기(종료일 추정). */
export function fmtDateRange(
  start: string | null | undefined,
  tier?: string | null,
  drawSize?: number | null,
): string {
  const s = String(start ?? "");
  if (s.length < 8) return "";
  const y = Number(s.slice(0, 4));
  const m = Number(s.slice(4, 6));
  const d = Number(s.slice(6, 8));
  const sd = new Date(Date.UTC(y, m - 1, d));
  if (Number.isNaN(sd.getTime())) return fmtDate(start);
  const dur = tourneyDurationDays(tier, drawSize);
  const ed = new Date(sd.getTime() + (dur - 1) * 86_400_000);
  const pad = (n: number) => String(n).padStart(2, "0");
  const startStr = `${y}.${pad(m)}.${pad(d)}`;
  const endMD = `${pad(ed.getUTCMonth() + 1)}.${pad(ed.getUTCDate())}`;
  const endStr = ed.getUTCFullYear() === y ? endMD : `${ed.getUTCFullYear()}.${endMD}`;
  return `${startStr} – ${endStr}`;
}

/** 시드 표기 " [N]" (없으면 빈 문자열). */
export function seedSuffix(seed: number | null | undefined): string {
  return seed ? ` [${seed}]` : "";
}

/** IOC + 이름 (국기는 이미지 컴포넌트로 별도 렌더). 스코어보드 텍스트용. */
export function nameWithIoc(name: string | null, ioc: string | null, fallbackId: number): string {
  const cc = ioc ? `${ioc.toUpperCase()} ` : "";
  return `${cc}${name ?? `선수 #${fallbackId}`}`;
}
