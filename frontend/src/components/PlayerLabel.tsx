import { flagEmoji } from "../lib/flags";

interface Props {
  name: string | null;
  ioc: string | null;
  id: number;
  seed?: number | null;
  className?: string;
}

/** 국기 + IOC 3글자 + 이름(+시드). */
export default function PlayerLabel({ name, ioc, id, seed, className = "" }: Props) {
  const flag = flagEmoji(ioc);
  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`}>
      {flag && <span className="leading-none">{flag}</span>}
      {ioc && <span className="text-[0.65rem] font-semibold text-neutral-400 tabular-nums">{ioc.toUpperCase()}</span>}
      <span className="truncate">{name ?? `#${id}`}</span>
      {seed ? <span className="text-[0.65rem] text-neutral-400">[{seed}]</span> : null}
    </span>
  );
}
