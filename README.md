# tennis-records

테니스 경기 기록 웹앱 — 그랜드슬램 / 1000 / 500 / 250 / 투어 파이널스 / 올림픽 **단식**의
역대 결과·전적·우승자 + 경기별 상세(세트 스코어보드 + 스탯 바, Tier 1).

> 전체 기획은 [`PROJECT_BRIEF.md`](./PROJECT_BRIEF.md) 참고. 본 README는 개발 실행 가이드.

## 구조

```
tennis-records/
├─ PROJECT_BRIEF.md      # 기획 아티팩트 (v6)
├─ backend/              # FastAPI + ETL (Python)
│  ├─ app/               # API 서버
│  └─ etl/               # CSV → tennis.db 파이프라인
├─ data/
│  ├─ raw/{atp,wta}/     # 원천 CSV (gitignore)
│  ├─ seed/              # tournament_tiers.csv 등 큐레이션 시드
│  └─ tennis.db          # 단일 산출물 (gitignore)
└─ frontend/             # React + Vite + Tailwind
```

## 빠른 시작

### 1. 백엔드 / ETL

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# ETL: 원천 CSV 다운로드 → tennis.db 빌드
python -m etl.fetch_sources       # atp + wta 연도별 매치 + 선수 + 랭킹 CSV → ../data/raw/
python -m etl.td_supplement       # 보조 소스(tennis-data.co.uk)로 진행 시즌 보강 (아래 ⚠️)
python -m etl.build_db            # 정규화 + score 파싱 → ../data/tennis.db
python -m etl.build_olympics      # 올림픽 금/은/동 추출
python -m etl.build_rankings      # 시즌별 연말/최고 랭킹 (랭킹 추이 차트용)
python -m etl.validate            # 정합성 리포트

# API 서버
uvicorn app.main:app --reload --port 8000
```

`score_parser` 단위 테스트:

```powershell
cd backend
pytest etl/tests -q
```

### 2. 프론트엔드

```powershell
cd frontend
npm install
npm run dev          # http://localhost:5173 (API 프록시 → :8000)
```

## 데이터 출처 / 라이선스

- Jeff Sackmann `tennis_atp` / `tennis_wta` — **CC BY-NC-SA 4.0** (저작자 표시 + 비상업 +
  동일조건, 푸터/README 명시 필수)
- [`Aneeshers/tennis-sackmann-archive`](https://github.com/Aneeshers/tennis-sackmann-archive) —
  위 데이터의 아카이브 미러 (2026-06 스냅샷, 동일 라이선스)
- [tennis-data.co.uk](http://tennis-data.co.uk/data.php) — 2026-06 이후 진행 시즌 보조 소스 (비상업 이용)

### ⚠️ 1차 소스 중단 (2026-06)

`JeffSackmann/tennis_atp` · `tennis_wta` 리포지토리가 **비공개 처리되어 모든 URL 이 404** 다.
이 때문에 2026 시즌은 롤랑가로스(5월)까지만 받아져 있었다.

- 과거분: `fetch_sources` 가 1차 소스 404 시 **아카이브 미러로 자동 폴백** (`[mirror]` 표시).
- 2026-06 이후: 미러에도 없으므로 **`etl.td_supplement`** 가 tennis-data.co.uk 의 연도별
  xlsx 를 받아 Sackmann 스키마 CSV(`data/raw/{tour}/{tour}_matches_{year}_td.csv`)로 변환한다.
  `build_db` 의 글롭이 그대로 집어가므로 적재 경로 변경은 없다.
- 식별자 매핑은 두 소스가 겹치는 구간(2023~2026-05)에서 학습하고, 결과를 감사용으로
  `data/seed/td_{tournament,player}_map.csv` 에 남긴다. 자동 매핑이 틀리거나 비는 건
  `data/seed/td_{tournament,player}_overrides.csv` 로 덮어쓴다.
- **보조 소스에 없는 값**: 서브 스탯(ace/df/svpt…)·경기 시간·시드·타이브레이크 득점.
  → 해당 경기는 스탯 바/시드가 비고, 스코어보드는 `7-6` 까지만 나온다.

### 등급(1000/500/250) 교차검증

1차 소스의 `tourney_level` 코드는 연도별 승격/강등을 못 따라간다(ATP 500 고정셋,
WTA `P`→500 일괄). `td_supplement` 가 TD 의 등급 라벨에서
`data/seed/td_tournament_tiers.csv` 를 생성하고, `derive_tier` 가 이를 최우선 적용한다.
TD 라벨이 틀린 건은 `data/seed/tournament_tiers.csv`(수동)로 되돌린다.

고쳐진 예: ATP Doha(2024까지 250)·Hamburg(2021–24 250)·Dallas·Munich(2025+ 500),
WTA Doha↔Dubai 1000 교차, Guadalajara(연도별 250/500/1000), **2022 WTA 1000 8개**
(이전엔 3개만 잡혔다).

## 개발 현황

- [x] **Phase 0** — 스캐폴딩, score_parser 확정, 스키마/필터 골격
- [x] **Phase 1** — 그랜드슬램 남·녀 + 매치 디테일 + 토글 (이름 정규화 포함)
- [x] **Phase 2** — H2H(서피스/tier/라운드 분해) + 기록(우승/결승) + 선수 프로필 + 검색
- [x] **Phase 3** — 1000(ATP 1990~ 정규화) + 파이널스(Tour Finals 계보 통합) + 토너먼트 트리 대진표(국기·접기)
- [x] **Phase 4+5** — ATP 500/250(2009~, 500 고정셋 큐레이션) + WTA 1000/500/250(2021~, level 코드) + 선수 상세 페이지(플레이스타일·서피스·등급별 커리어)
- [x] **Phase 6** — 올림픽 메달(남녀 금은동·국기) + 에디션 목록
- [x] **Phase 7** — 랭킹 추이 차트(Recharts), 헤더 선수 검색, 토너먼트 대진 연결선, 달력순 정렬
- [x] **Phase 8** — 1차 소스 중단 대응: 아카이브 미러 폴백 + tennis-data.co.uk 보조 ETL
  (2026 윔블던·US오픈 등 하반기 43개 대회 1,913경기), tier 분류 교정(팀 대항전·소련선수권),
  올림픽 메달 공백 보강(1996 WTA 전체, 2000·2004 WTA 동메달)

### 데이터 자동 갱신
주간 스케줄러로 진행 시즌 CSV 재수신 + 보조 소스 보강 + DB 재빌드 + GS 레퍼런스 재생성:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_update_task.ps1   # 매주 월 05:00 등록
powershell -ExecutionPolicy Bypass -File scripts\update_data.ps1            # 수동 1회 실행
```

> **ETL 주의:** `build_db` 는 `tennis.db` 에 쓰기 락이 필요하므로, **API 서버(uvicorn)를 먼저 멈춘 뒤** 실행할 것.
> 실행 중이면 `database is locked` 로 스키마 적용이 조용히 실패한다.

> ⚠️ H2H/기록은 현재 적재 범위(ATP GS·1000(1990~)·500/250(2009~)·FINALS·OLYMPICS +
> WTA GS·FINALS·OLYMPICS 전기간·1000/500/250 2021~)만 반영.
> **WTA 2021 이전 등급(Premier/Tier)·ATP 2009 이전 투어 대회는 의도적 미적재**(§2.2, §13)
> 이므로 그 구간의 상대전적·기록 수치는 비어 있다.

> ⚠️ 2026 하반기(6월~) 경기는 보조 소스에서 왔으므로 **시드·서브 스탯·경기 시간이 없다.**
> 랭킹 추이도 주간 스냅샷이 2026-06-08 에서 끊겨, 이후 시즌 값은 경기 단위 랭킹으로 보강한
> 근사값이다.
