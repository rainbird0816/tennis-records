// API 응답 타입 (backend §7 에 대응). Phase 진행하며 확장.

export type Tour = "atp" | "wta";
export type Tier = "GS" | "1000" | "500" | "250" | "FINALS" | "OLYMPICS";
export type Outcome = "completed" | "RET" | "W/O" | "DEF";

export interface Availability {
  tour: Tour;
  min_season: number;
  max_season: number;
  n_tournaments: number;
}

export interface CategoryInfo {
  tier: Tier;
  availability: Availability[];
}

export interface SetScore {
  set_no: number;
  w_games: number;
  l_games: number;
  tb_w: number | null;
  tb_l: number | null;
}

export interface StatPair {
  w: number | null;
  l: number | null;
}

export interface PlayerHit {
  tour: Tour;
  player_id: number;
  full_name: string;
  ioc: string | null;
}

export interface H2HBreakdown {
  p1_wins: number;
  p2_wins: number;
  surface?: string;
  tier?: string;
  round?: string;
}

export interface H2HMatch {
  match_id: string;
  tourney_id: string;
  round: string;
  score: string | null;
  surface: string | null;
  season: number;
  tier: string;
  tournament_name: string;
  winner_id: number;
  loser_id: number;
  winner_name: string | null;
  loser_name: string | null;
}

export interface H2HResult {
  tour: Tour;
  p1: number;
  p2: number;
  p1_name: string | null;
  p2_name: string | null;
  summary: { total: number; p1_wins: number; p2_wins: number };
  by_surface: H2HBreakdown[];
  by_tier: H2HBreakdown[];
  by_round: H2HBreakdown[];
  matches: H2HMatch[];
}

export interface RecordLeader {
  player_id: number;
  full_name: string | null;
  n: number;
}

export interface PlayerProfile {
  player: {
    tour: Tour;
    player_id: number;
    full_name: string;
    hand: string | null;
    dob: string | null;
    ioc: string | null;
    height_cm: number | null;
  };
  record: { wins: number | null; losses: number | null };
}

export interface Title {
  season: number;
  name: string;
  tier: string;
  surface: string | null;
  runnerup_id: number;
  score: string | null;
}

export interface LatestChampion {
  season: number;
  tourney_id: string;
  champion_id: number;
  champion_name: string | null;
}

export interface Series {
  name: string;
  seasons: number;
  first_season: number;
  last_season: number;
  latest_champion: LatestChampion | null;
}

export interface Champion {
  season: number;
  name: string;
  surface: string | null;
  tourney_id: string;
  champion_id: number;
  runnerup_id: number;
  champion_name: string | null;
  runnerup_name: string | null;
  score: string | null;
}

export interface MatchRow {
  match_id: string;
  round: string;
  round_order: number;
  best_of: number | null;
  winner_id: number;
  loser_id: number;
  winner_seed: number | null;
  loser_seed: number | null;
  winner_rank: number | null;
  loser_rank: number | null;
  score: string | null;
  outcome: Outcome;
  minutes: number | null;
  has_stats: number;
  winner_name: string | null;
  loser_name: string | null;
  winner_ioc: string | null;
  loser_ioc: string | null;
}

export interface TournamentMeta {
  tour: Tour;
  tourney_id: string;
  name: string;
  tier: Tier;
  surface: string | null;
  draw_size: number | null;
  season: number;
  start_date: string | null;
}

export interface TournamentDetail {
  tournament: TournamentMeta;
  matches: MatchRow[];
}

export interface MatchDetail {
  match_id: string;
  tour: Tour;
  tourney_id: string;
  round: string;
  best_of: number | null;
  winner_id: number;
  loser_id: number;
  winner_name: string | null;
  loser_name: string | null;
  winner_ioc: string | null;
  loser_ioc: string | null;
  tournament_name: string | null;
  tier: Tier | null;
  season: number | null;
  surface: string | null;
  winner_seed: number | null;
  loser_seed: number | null;
  winner_rank: number | null;
  loser_rank: number | null;
  score: string | null;
  outcome: Outcome;
  minutes: number | null;
  has_stats: boolean;
  sets: SetScore[];
  stats: Record<string, StatPair> | null;
}
