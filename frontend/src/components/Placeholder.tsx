// Phase 진행 전 자리표시 컴포넌트들의 공통 베이스.
export function Placeholder({ name, note }: { name: string; note?: string }) {
  return (
    <div className="rounded-lg border border-dashed border-neutral-300 bg-white/60 p-4 text-sm text-neutral-500">
      <span className="font-mono font-medium text-neutral-700">{name}</span>
      {note && <span className="ml-2">— {note}</span>}
    </div>
  );
}
