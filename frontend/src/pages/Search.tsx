import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { PlayerHit, Tour } from "../api/types";
import SearchBar from "../components/SearchBar";
import TourToggle from "../components/TourToggle";

/** /search — 선수 검색 → 프로필 이동 (§9.1). */
export default function Search() {
  const [tour, setTour] = useState<Tour>("atp");
  const navigate = useNavigate();

  const go = (p: PlayerHit) => navigate(`/player/${p.tour}/${p.player_id}`);

  return (
    <div className="max-w-xl">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">선수 검색</h1>
        <TourToggle value={tour} onChange={setTour} />
      </div>
      <SearchBar tour={tour} placeholder="이름으로 검색…" onSelect={go} />
      <p className="text-xs text-neutral-400 mt-2">선수를 선택하면 프로필로 이동합니다.</p>
    </div>
  );
}
