import { Link, Outlet, useNavigate } from "react-router-dom";
import SearchBar from "./components/SearchBar";

const NAV = [
  { to: "/category/GS", label: "Grand Slam" },
  { to: "/category/1000", label: "1000" },
  { to: "/category/500", label: "500" },
  { to: "/category/250", label: "250" },
  { to: "/category/FINALS", label: "Finals" },
  { to: "/category/OLYMPICS", label: "Olympics" },
];

export default function App() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-court text-white">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center gap-4 flex-wrap">
          <Link to="/" className="font-bold text-lg tracking-tight">
            🎾 tennis-records
          </Link>
          <nav className="flex gap-4 text-sm">
            {NAV.map((n) => (
              <Link key={n.to} to={n.to} className="hover:underline">
                {n.label}
              </Link>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-4 text-sm">
            <Link to="/h2h" className="hover:underline">H2H</Link>
            <Link to="/records/GS" className="hover:underline">기록</Link>
            <div className="w-44 text-neutral-900">
              <SearchBar
                placeholder="선수 검색…"
                onSelect={(p) => navigate(`/player/${p.tour}/${p.player_id}`)}
              />
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 mx-auto max-w-6xl w-full px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t text-xs text-neutral-500 py-4 text-center">
        데이터: Jeff Sackmann tennis_atp / tennis_wta ·{" "}
        <span className="font-medium">CC BY-NC-SA 4.0</span> (비상업·동일조건)
      </footer>
    </div>
  );
}
