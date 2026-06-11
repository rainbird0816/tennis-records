interface Props {
  label: string;
  /** 승자/패자 값 (이미 표시용으로 가공된 수치). */
  w: number | null;
  l: number | null;
  /** % 단위 등 접미사 */
  suffix?: string;
}

/** 서브/리턴/BP 등 좌우 대조 바. has_stats=1(1991+) 경기에서만. §8 */
export default function StatCompareBar({ label, w, l, suffix = "" }: Props) {
  if (w == null && l == null) return null;
  const wv = w ?? 0;
  const lv = l ?? 0;
  const total = wv + lv || 1;
  const wPct = (wv / total) * 100;

  return (
    <div className="py-1.5">
      <div className="flex justify-between text-xs text-neutral-600 mb-0.5">
        <span className="font-medium text-court">{wv}{suffix}</span>
        <span>{label}</span>
        <span className="font-medium text-neutral-500">{lv}{suffix}</span>
      </div>
      <div className="flex h-2 rounded overflow-hidden bg-neutral-200">
        <div className="bg-court" style={{ width: `${wPct}%` }} />
        <div className="bg-neutral-400" style={{ width: `${100 - wPct}%` }} />
      </div>
    </div>
  );
}
