"""중앙 설정 — 경로/상수. PROJECT_BRIEF §10 디렉토리 구조 기준."""
from __future__ import annotations

import os
from pathlib import Path

# backend/app/config.py → backend/ → tennis-records/ (repo root)
ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
SEED_DIR = DATA_DIR / "seed"

# 빌드 산출물 — 단일 읽기 전용 SQLite (§4)
DB_PATH = Path(os.environ.get("TENNIS_DB", DATA_DIR / "tennis.db"))

# 정규화 tier 집합 (§3)
TIERS = ("GS", "1000", "500", "250", "FINALS", "OLYMPICS")

# WTA 등급(1000/500/250) 적재 시작 시즌 — 옵션 B (§2.2)
WTA_GRADE_MIN_SEASON = 2021

# ATP Masters 1000 적재 시작 시즌 — 마스터스 시리즈 출범(1990) 이전 'M' 이벤트 제외 (§1.2)
ATP_1000_MIN_SEASON = 1990

# 세부 서브 통계가 채워지기 시작하는 시즌 (§1.3, §12)
STATS_MIN_SEASON = 1991
