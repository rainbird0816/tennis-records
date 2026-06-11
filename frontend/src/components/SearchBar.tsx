import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { PlayerHit, Tour } from "../api/types";

interface Props {
  tour?: Tour;
  placeholder?: string;
  onSelect: (p: PlayerHit) => void;
}

/** 디바운스 선수 검색 + 드롭다운 (§9.1). */
export default function SearchBar({ tour, placeholder = "선수 검색…", onSelect }: Props) {
  const [text, setText] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(text.trim()), 250);
    return () => clearTimeout(t);
  }, [text]);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const { data } = useQuery({
    queryKey: ["search", debounced, tour],
    queryFn: () => api<{ players: PlayerHit[] }>("/search", { q: debounced, tour }),
    enabled: debounced.length >= 2,
  });

  return (
    <div ref={boxRef} className="relative">
      <input
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        placeholder={placeholder}
        className="w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-court"
      />
      {open && data && data.players.length > 0 && (
        <ul className="absolute z-10 mt-1 w-full rounded-lg border bg-white shadow-lg max-h-64 overflow-auto">
          {data.players.map((p) => (
            <li key={`${p.tour}-${p.player_id}`}>
              <button
                onClick={() => {
                  onSelect(p);
                  setText(p.full_name);
                  setOpen(false);
                }}
                className="w-full text-left px-3 py-2 text-sm hover:bg-neutral-100 flex justify-between"
              >
                <span>{p.full_name}</span>
                <span className="text-xs text-neutral-400">
                  {p.tour.toUpperCase()} {p.ioc && `· ${p.ioc}`}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
