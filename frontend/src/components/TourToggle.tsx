import type { Tour } from "../api/types";

interface Props {
  value: Tour;
  onChange: (t: Tour) => void;
  /** 가용하지 않은 tour 는 비활성 (§9.3) */
  available?: Tour[];
}

export default function TourToggle({ value, onChange, available }: Props) {
  const tours: Tour[] = ["atp", "wta"];
  return (
    <div className="inline-flex rounded-lg border overflow-hidden text-sm">
      {tours.map((t) => {
        const disabled = available && !available.includes(t);
        return (
          <button
            key={t}
            disabled={disabled}
            onClick={() => onChange(t)}
            className={[
              "px-4 py-1.5 font-medium transition",
              value === t ? "bg-court text-white" : "bg-white text-neutral-700",
              disabled ? "opacity-40 cursor-not-allowed" : "hover:bg-court-light hover:text-white",
            ].join(" ")}
          >
            {t.toUpperCase()}
          </button>
        );
      })}
    </div>
  );
}
