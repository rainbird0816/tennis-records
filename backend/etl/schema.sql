-- tennis.db 스키마 (PROJECT_BRIEF §5). build_db.py 가 멱등 적용.
PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS champions;
DROP TABLE IF EXISTS match_sets;
DROP TABLE IF EXISTS olympic_medals;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS tournaments;
DROP TABLE IF EXISTS players;

CREATE TABLE players(
  tour TEXT, player_id INTEGER, full_name TEXT, hand TEXT, dob TEXT,
  ioc TEXT, height_cm INTEGER, PRIMARY KEY(tour, player_id)
);

CREATE TABLE tournaments(
  tour TEXT, tourney_id TEXT, name TEXT, tier TEXT, level_raw TEXT,
  surface TEXT, draw_size INTEGER, season INTEGER, start_date TEXT,
  location TEXT, country TEXT, PRIMARY KEY(tour, tourney_id)
);

CREATE TABLE matches(
  match_id TEXT PRIMARY KEY, tour TEXT, tourney_id TEXT, match_num INTEGER,
  round TEXT, round_order INTEGER, best_of INTEGER,
  winner_id INTEGER, loser_id INTEGER,
  winner_seed INTEGER, loser_seed INTEGER, winner_rank INTEGER, loser_rank INTEGER,
  score TEXT,            -- 원문 보존
  outcome TEXT,          -- 'completed' | 'RET' | 'W/O' | 'DEF'
  minutes INTEGER, has_stats INTEGER DEFAULT 0,
  w_ace INTEGER, w_df INTEGER, w_svpt INTEGER, w_1stIn INTEGER, w_1stWon INTEGER,
  w_2ndWon INTEGER, w_SvGms INTEGER, w_bpSaved INTEGER, w_bpFaced INTEGER,
  l_ace INTEGER, l_df INTEGER, l_svpt INTEGER, l_1stIn INTEGER, l_1stWon INTEGER,
  l_2ndWon INTEGER, l_SvGms INTEGER, l_bpSaved INTEGER, l_bpFaced INTEGER,
  FOREIGN KEY(tour, tourney_id) REFERENCES tournaments(tour, tourney_id)
);

-- 세트별 게임 스코어 (score 파싱 결과; 스코어보드 렌더 소스)
CREATE TABLE match_sets(
  match_id TEXT, set_no INTEGER,
  w_games INTEGER, l_games INTEGER,
  tb_w INTEGER, tb_l INTEGER,
  PRIMARY KEY(match_id, set_no)
);

-- 올림픽 메달 (build_olympics.py, §12)
CREATE TABLE olympic_medals(
  tour TEXT, season INTEGER, medal TEXT,  -- 'gold' | 'silver' | 'bronze'
  player_id INTEGER,
  PRIMARY KEY(tour, season, medal)
);

CREATE INDEX idx_m_tourney ON matches(tour, tourney_id);
CREATE INDEX idx_m_winner  ON matches(tour, winner_id);
CREATE INDEX idx_m_loser   ON matches(tour, loser_id);
CREATE INDEX idx_t_tier    ON tournaments(tier, tour, season);

CREATE VIEW champions AS
SELECT t.tour, t.tourney_id, t.name, t.tier, t.season, t.surface,
       m.winner_id AS champion_id, m.loser_id AS runnerup_id, m.score
FROM matches m
JOIN tournaments t ON t.tour = m.tour AND t.tourney_id = m.tourney_id
WHERE t.tier <> 'OLYMPICS' AND m.round = 'F';
