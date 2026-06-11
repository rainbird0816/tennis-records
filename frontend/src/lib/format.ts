/** "YYYYMMDD" → "YYYY.MM.DD" (대회 시작일). 잘못된 값은 빈 문자열. */
export function fmtDate(yyyymmdd: string | null | undefined): string {
  const s = String(yyyymmdd ?? "");
  if (s.length < 8) return "";
  return `${s.slice(0, 4)}.${s.slice(4, 6)}.${s.slice(6, 8)}`;
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
