import { createBrowserRouter } from "react-router-dom";
import App from "./App";
import Home from "./pages/Home";
import Category from "./pages/Category";
import Overview from "./pages/Overview";
import Series from "./pages/Series";
import Bracket from "./pages/Bracket";
import Olympics from "./pages/Olympics";
import Match from "./pages/Match";
import Player from "./pages/Player";
import H2H from "./pages/H2H";
import Records from "./pages/Records";
import Search from "./pages/Search";

// 사이트맵 §9.1
export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <Home /> },
      { path: "category/:tier", element: <Category /> },
      { path: "overview/:tier", element: <Overview /> },
      { path: "series/:slug", element: <Series /> },
      { path: "series/:slug/:season", element: <Bracket /> },
      { path: "olympics/:season", element: <Olympics /> },
      { path: "match/:matchId", element: <Match /> },
      { path: "player/:tour/:playerId", element: <Player /> },
      { path: "h2h", element: <H2H /> },
      { path: "records/:tier", element: <Records /> },
      { path: "search", element: <Search /> },
    ],
  },
]);
