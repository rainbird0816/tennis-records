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

- Jeff Sackmann [`tennis_atp`](https://github.com/JeffSackmann/tennis_atp) / [`tennis_wta`](https://github.com/JeffSackmann/tennis_wta)
- **CC BY-NC-SA 4.0** — 저작자 표시 + 비상업 + 동일조건. 푸터/README 명시 필수.

## 개발 현황

- [x] **Phase 0** — 스캐폴딩, score_parser 확정, 스키마/필터 골격
- [x] **Phase 1** — 그랜드슬램 남·녀 + 매치 디테일 + 토글 (이름 정규화 포함)
- [x] **Phase 2** — H2H(서피스/tier/라운드 분해) + 기록(우승/결승) + 선수 프로필 + 검색
- [x] **Phase 3** — 1000(ATP 1990~ 정규화) + 파이널스(Tour Finals 계보 통합) + 토너먼트 트리 대진표(국기·접기)
- [x] **Phase 4+5** — ATP 500/250(2009~, 500 고정셋 큐레이션) + WTA 1000/500/250(2021~, level 코드) + 선수 상세 페이지(플레이스타일·서피스·등급별 커리어)
- [x] **Phase 6** — 올림픽 메달(남녀 금은동·국기) + 에디션 목록
- [x] **Phase 7** — 랭킹 추이 차트(Recharts), 헤더 선수 검색, 토너먼트 대진 연결선, 달력순 정렬

### 데이터 자동 갱신
주간 스케줄러로 진행 시즌 CSV 재수신 + DB 재빌드:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_update_task.ps1   # 매주 월 05:00 등록
powershell -ExecutionPolicy Bypass -File scripts\update_data.ps1            # 수동 1회 실행
```

> **ETL 주의:** `build_db` 는 `tennis.db` 에 쓰기 락이 필요하므로, **API 서버(uvicorn)를 먼저 멈춘 뒤** 실행할 것.
> 실행 중이면 `database is locked` 로 스키마 적용이 조용히 실패한다.

> ⚠️ H2H/기록은 현재 적재 범위(GS·1000·FINALS·OLYMPICS + WTA 2021+ 등급)만 반영.
> ATP 500/250(Phase 4·5)이 적재되면 상대전적·기록 수치가 그만큼 채워진다.
