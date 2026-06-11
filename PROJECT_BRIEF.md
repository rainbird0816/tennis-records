# PROJECT_BRIEF.md — tennis-records (테니스 경기 기록 웹앱) · v6

> 그랜드슬램 / 1000 / 500 / 250 / 투어 파이널스 / 올림픽 단식의 역대 결과·전적·우승자 +
> **경기별 결과·분석(매치 디테일, Tier 1)** 웹앱.
> 성별(옵션 B): ATP 전 카테고리·전 기간 / WTA 슬램·올림픽·파이널스(전 기간) + 1000/500/250(2021+).
> 개발 워크플로우: VS Code + Claude CLI. 본 문서를 CLI 세션의 기획 아티팩트로 사용.
>
> v6 변경점: **매치 분석을 Tier 1로 단일화** — 샷 차팅(T3)·포인트별 모멘텀(T2) 모두 커밋 범위에서 제외.
>            대신 **세트별 게임 스코어(+타이브레이크)** 를 `score` 문자열 파싱으로 추가(전 경기·1968~).
>            → slam_pointbypoint / MatchChartingProject 소스, points.db, 이름 정합 ETL 전부 제거(단일 tennis.db).

---

## 0. 핵심 원칙 (CLI 작업 규칙)
- **원천 CSV는 절대 모델 컨텍스트에 통째로 올리지 않는다.** head/columns/describe/value_counts 요약만.
- **Depth-first 슬라이스**: 한 카테고리를 끝까지 완성 후 확장.
- **API 키 의존 서비스 미사용.** 공개 CSV(원샷 다운로드)에서 ETL.
- DB는 빌드 타임 생성 **읽기 전용 SQLite 단일 파일** `tennis.db`.

---

## 1. 개요 / 범위
### 1.1 목표
카테고리 진입 → 역대 우승자·연도별 대진·선수 전적·H2H·기록 + **개별 경기 상세(Tier 1)**.

### 1.2 카테고리·성별 커버리지 (옵션 B)
| 카테고리 | ATP(남) | WTA(여) |
|---|---|---|
| Grand Slam | 1968~ | **전 기간** |
| Olympics | 1988~ | **1988~** |
| Tour Finals | 전 기간 | **전 기간** |
| 1000 | 1990~ | **2021~** |
| 500 / 250 | 2019+/2009–18 + (선택)이전 | **2021~** |

- 보류(고려): 2021 이전 WTA 등급(2009–2020 Premier, ~2008 Tier). §13.
- 데이터 없는 (tier, tour)는 토글 숨김(§9.3).

### 1.3 매치 분석 = Tier 1 (단일) ★v6
- 소스: **메인 `*_matches_*.csv`만**(이미 적재). 추가 소스·별도 DB 없음.
- 구성:
  - **세트별 스코어보드**: `score` 문자열 파싱 → 세트별 게임 스코어 + 타이브레이크. **전 경기(1968~)** 표시.
  - **스탯 대조 바**: 서브/리턴/브레이크포인트 등. **1991+** 채워짐(이전은 스코어보드만).
- 제외(커밋 안 함): 포인트별 모멘텀/서브속도/랠리(T2, 슬램 2011+에서만 가능), 샷 차팅(T3).
  → 둘 다 §13에 "원하면 추가" 항목으로만 보존.

### 1.4 트레이드오프 (명시)
- WTA 1000/500/250 = 2021+ → 2021 이전 여자 선수 투어 타이틀 미반영(프로필 안내).
- 매치 분석은 Tier 1까지 → 모멘텀 곡선·서브 속도·랠리 길이는 제공 안 함(포인트별 데이터 필요 항목).
- 세부 서브 통계는 1991+만(스코어보드는 그 이전도 가능).

### 1.5 비목표
- 실시간 스코어/베팅/예측/로그인 없음. 복식·혼복·챌린저/ITF·팀 대항전 제외. 포인트별·샷 단위 분석 제외.

---

## 2. 데이터 소스
### 2.1 ATP — `tennis_atp`
- `atp_matches_{YYYY}.csv`(1968~), `atp_players.csv`, `atp_rankings_*.csv`, `matches_data_dictionary.txt`. 통계 1991+.

### 2.2 WTA — `tennis_wta` (ATP 동일 포맷)
- 적재 필터: GS/OLYMPICS/FINALS 전 기간 / 1000·500·250은 **season≥2021만**.
- ⚠️ player_id가 ATP와 충돌 → (tour, player_id) 복합키.

### 2.3 공통 라이선스
- CC BY-NC-SA 4.0 — 저작자 표시 + 비상업 + 동일조건. 푸터/README 명시.

### 2.4 보조(선택)
- 위키피디아 연도별 표로 tier·대회 메타(개최지·국가)·올림픽 도시 큐레이션.

> (제거됨) slam_pointbypoint / MatchChartingProject — 모멘텀·샷 분석용이며 현재 범위 밖. §13.

---

## 3. 카테고리 매핑 (tour 인식형)
정규화 tier: `GS·1000·500·250·FINALS·OLYMPICS` (tour 컬럼이 ATP/WTA 구분, 라벨만 분기).
도출: name "Olympic"→OLYMPICS / G→GS / 파이널스→FINALS / ATP M→1000 / 나머지→`tournament_tiers.csv`(WTA 2021+만).
보류: WTA 2009–2020 Premier(Mand.+5→1000, Premier→500, Int'l→250), ~2008 Tier, ATP pre-2009.

---

## 4. 기술 스택
| 레이어 | 선택 |
|---|---|
| 백엔드 | Python 3.11 + FastAPI + Uvicorn |
| DB | **SQLite 단일 파일 `tennis.db`** |
| ETL | Python (pandas) — 점수 문자열 파서 포함 |
| 프론트 | React + Vite + TanStack Query + React Router |
| 차트/테이블 | Recharts(스탯 바·랭킹 추이) / TanStack Table |
| 브래킷/메달/스코어보드 | 커스텀 SVG·Flexbox |
| 스타일 | Tailwind CSS |

---

## 5. 데이터 모델 (단일 `tennis.db`)
```sql
CREATE TABLE players(    tour TEXT, player_id INTEGER, full_name TEXT, hand TEXT, dob TEXT,
                         ioc TEXT, height_cm INTEGER, PRIMARY KEY(tour,player_id));
CREATE TABLE tournaments(tour TEXT, tourney_id TEXT, name TEXT, tier TEXT, level_raw TEXT,
                         surface TEXT, draw_size INTEGER, season INTEGER, start_date TEXT,
                         location TEXT, country TEXT, PRIMARY KEY(tour,tourney_id));
CREATE TABLE matches(    match_id TEXT PRIMARY KEY, tour TEXT, tourney_id TEXT, match_num INTEGER,
                         round TEXT, round_order INTEGER, best_of INTEGER,
                         winner_id INTEGER, loser_id INTEGER,
                         winner_seed INTEGER, loser_seed INTEGER, winner_rank INTEGER, loser_rank INTEGER,
                         score TEXT,            -- 원문 보존
                         outcome TEXT,          -- 'completed' | 'RET' | 'W/O' | 'DEF'
                         minutes INTEGER, has_stats INTEGER DEFAULT 0,  -- 서브 통계 존재(1991+)
                         w_ace INTEGER, w_df INTEGER, w_svpt INTEGER, w_1stIn INTEGER, w_1stWon INTEGER,
                         w_2ndWon INTEGER, w_SvGms INTEGER, w_bpSaved INTEGER, w_bpFaced INTEGER,
                         l_ace INTEGER, l_df INTEGER, l_svpt INTEGER, l_1stIn INTEGER, l_1stWon INTEGER,
                         l_2ndWon INTEGER, l_SvGms INTEGER, l_bpSaved INTEGER, l_bpFaced INTEGER,
                         FOREIGN KEY(tour,tourney_id) REFERENCES tournaments(tour,tourney_id));

-- 세트별 게임 스코어 (score 파싱 결과; 스코어보드 렌더 소스)
CREATE TABLE match_sets(
  match_id TEXT, set_no INTEGER,
  w_games INTEGER, l_games INTEGER,   -- 승자/패자 기준 게임 수
  tb_w INTEGER, tb_l INTEGER,         -- 타이브레이크 점수(없으면 NULL)
  PRIMARY KEY(match_id, set_no)
);

CREATE INDEX idx_m_tourney ON matches(tour,tourney_id);
CREATE INDEX idx_m_winner  ON matches(tour,winner_id);
CREATE INDEX idx_m_loser   ON matches(tour,loser_id);
CREATE INDEX idx_t_tier    ON tournaments(tier,tour,season);

CREATE VIEW champions AS
SELECT t.tour,t.tourney_id,t.name,t.tier,t.season,t.surface,
       m.winner_id AS champion_id, m.loser_id AS runnerup_id, m.score
FROM matches m JOIN tournaments t ON t.tour=m.tour AND t.tourney_id=m.tourney_id
WHERE t.tier<>'OLYMPICS' AND m.round='F';
```
> 올림픽 메달(금/은/동)은 별도 추출(§12). H2H·통산 우승 수는 쿼리(무거우면 요약 테이블).

---

## 6. ETL 파이프라인 (`backend/etl/`)
```
1) fetch_sources.py   # atp + wta 연도별 CSV → data/raw/{atp,wta}/
2) build_tiers.py     # tournament_tiers.csv → 1000/500/250 (WTA 2021+)
3) build_db.py        # 정규화(tour, player 네임스페이스, tier) + WTA 필터
                      #   + score 파서 → match_sets, outcome, has_stats → tennis.db
4) build_olympics.py  # 'Olympic' 식별 + 남녀 금/은/동
5) validate.py        # 행수·우승자/메달·라운드·tier·세트합 정합성 리포트
```
**score 파서 규칙**: 공백 분리 세트 → `W-L` + 선택 `(tb)`. `RET`/`W/O`/`DEF` 토큰 만나면
`outcome` 설정·이후 세트 중단. 어드밴티지(최종세트 타이브레이크 없음, 예 `70-68`)·미완 세트 허용.
규칙: CSV 본문 미첨부, `build_db.py` 멱등.

---

## 7. API 설계 (`/api`)
| Method · Path | 설명 |
|---|---|
| `GET /categories` | 6 카테고리 + (tier,tour) 가용/연도 |
| `GET /categories/{tier}?tour=` | 시리즈 대회 + latest_champion |
| `GET /tournaments/{tour}/{tourney_id}` | 대회 메타 + 라운드별 경기(브래킷) |
| `GET /series/{slug}/champions?tour=` | 역대 우승자 |
| `GET /olympics/{season}/medals` | 남·녀 금/은/동 |
| `GET /matches/{match_id}` | **세트별 스코어(match_sets) + 스탯(has_stats) + outcome** |
| `GET /players/{tour}/{player_id}` , `/titles?tier=` | 프로필·우승목록 |
| `GET /h2h?p1=&p2=` , `GET /records?tier=&tour=&metric=` , `GET /search?q=&tour=` | 상대전적·기록·검색 |

---

## 8. 매치 디테일 페이지 `/match/:matchId` (Tier 1) ★v6
- **헤더**: 양 선수(시드/랭킹), 라운드·대회·연도·서피스, 경기 시간, 최종 결과(승자·outcome).
- **세트별 스코어보드**(전 경기): 세트별 게임 스코어 행, 타이브레이크는 위첨자(예 7-6⁷⁻⁵), 승자 강조.
  - RET/W/O는 배지("기권"/"부전승")로 표기.
- **스탯 대조 바**(has_stats=1, 1991+): 1st 서브%, 1st/2nd 서브 득점%, 에이스, DF,
  브레이크포인트(전환/세이브), 서비스 게임 키핑, 리턴 득점, 총 득점, dominance ratio.
  - 통계 없는 경기엔 "세부 통계 미제공" 배지(스코어보드만).

---

## 9. 그 외 화면
### 9.1 사이트맵
`/` · `/category/:tier`(ATP/WTA 토글) · `/series/:slug` · `/series/:slug/:season`(브래킷) ·
`/olympics/:season` · `/match/:matchId` · `/player/:tour/:playerId` · `/h2h` · `/records/:tier` · `/search`.

### 9.2 시리즈 랜딩
대회 카드 + 각 **최신 우승자**(미개최면 직전 연도 배지). 카드→`/series/:slug`. ATP/WTA 토글.

### 9.3 토글 가용성
`/categories`가 (tier,tour) 유무 반환 → 빈 조합 토글 숨김/비활성.

### 9.4 선수 프로필 / H2H / 기록 / 올림픽 메달
프로필: 국적·손·신장·통산 승패 + 탭[개요/우승목록/서피스별 승률/랭킹추이/최고의 승리],
"WTA 등급 타이틀 2021+만" 안내. H2H: 서피스/라운드/tier 분해. 올림픽: 남녀 메달 테이블.

---

## 10. 디렉토리 구조
```
tennis-records/
├─ PROJECT_BRIEF.md
├─ backend/
│  ├─ app/{main.py, db.py, routers/}
│  ├─ etl/{fetch_sources, build_tiers, build_db, build_olympics, validate}.py
│  ├─ etl/score_parser.py               # score 문자열 → 세트/타이브레이크/outcome
│  └─ requirements.txt
├─ data/
│  ├─ raw/{atp,wta}/                     # gitignore
│  ├─ seed/tournament_tiers.csv          # (tour,season,대회)→1000/500/250
│  └─ tennis.db                          # 단일 산출물(gitignore)
└─ frontend/src/{pages, components(TourToggle, Bracket, SetScoreboard, StatCompareBar,
                  MedalTable, SeriesGrid, ChampionsTable, RankChart, SearchBar), api, App.tsx}
```

---

## 11. 개발 로드맵 (Depth-first)
- **Phase 0** 토대: 스캐폴딩, fetch(atp+wta), 사전검토(요약만), 스키마·WTA 필터·score_parser 확정.
- **Phase 1** 그랜드슬램 남·녀(전 기간) + **매치 디테일(세트 스코어보드 + 스탯 바)** + 토글 플러밍.
- **Phase 2** H2H + 기록.
- **Phase 3** 1000 + 파이널스(ATP 1990~ / WTA 2021~).
- **Phase 4** 500/250 현행(ATP 2019+ / WTA 2021+).
- **Phase 5** ATP 500/250 백필(2009–2018).
- **Phase 6** 올림픽(남·녀) 메달·대진.
- **Phase 7** 다듬기: 검색 autocomplete, 브래킷 연결선, 차트.
- **고려/선택**: WTA 2021 이전 백필, ATP pre-2009, (원하면)포인트별 모멘텀 T2 재도입, sql.js 정적 배포.

---

## 12. 데이터 주의사항 (체크리스트)
- [ ] ATP·WTA player_id 충돌 → (tour, player_id) 복합키.
- [ ] WTA 등급(1000/500/250)은 2021+만 적재(빌드 필터).
- [ ] **score 파서**: RET/W/O/DEF 처리, 타이브레이크 괄호, 어드밴티지 최종세트(타이브레이크 없는 70-68 등), 미완 세트.
- [ ] 세부 서브 통계는 1991+만(has_stats). 이전 경기는 스코어보드만.
- [ ] 올림픽 식별 name "Olympic" / 메달 금=결승승·은=결승패·동=동메달전 승 / best_of 변천.
- [ ] 파이널스 우승자 = round='F' + RR 구조 검증.
- [ ] 빈 (tier, tour) 조합 → 프론트 토글 숨김.

---

## 13. 향후 확장 / 고려 대상
- (원하면)**포인트별 모멘텀 T2**: `tennis_slam_pointbypoint`(슬램 2011+) → 모멘텀 곡선·서브속도·랠리.
  별도 points.db + 이름 정합 ETL 필요. 현재 범위 밖.
- 샷 차팅 T3(`tennis_MatchChartingProject`) — 범위 밖.
- WTA 2021 이전 등급 백필(Premier/Tier), ATP pre-2009, 복식·혼복, 시즌 캘린더, 국가별 통계.
- sql.js 정적 빌드(단일 tennis.db) → Vercel 정적 호스팅 호환.

---

## 14. 출처
- Jeff Sackmann *tennis_atp* / *tennis_wta* (CC BY-NC-SA 4.0)
- 컬럼 정의: tennis_atp `matches_data_dictionary.txt`
- 카테고리 구조: 위키피디아 연도별 ATP 1000/500/250, WTA 현행/Premier, Tennis at the Summer Olympics
