"""읽기 전용 SQLite 접근 헬퍼 (단일 tennis.db, §4)."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from .config import DB_PATH


def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"tennis.db 가 없습니다: {DB_PATH}\n"
            "먼저 ETL 을 실행하세요:  python -m etl.build_db"
        )
    # 읽기 전용 모드로 오픈 (빌드타임 생성물, 런타임 변경 금지)
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def query(sql: str, params: tuple | dict = ()) -> list[dict]:
    """SELECT 실행 → dict 리스트."""
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def query_one(sql: str, params: tuple | dict = ()) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None
