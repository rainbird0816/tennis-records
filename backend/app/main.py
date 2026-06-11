"""FastAPI 엔트리포인트 — /api 라우터 마운트 (§7)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import categories, matches, misc, players, tournaments

app = FastAPI(
    title="tennis-records API",
    version="0.1.0",
    description="ATP/WTA 단식 역대 결과·전적·매치 디테일 (Tier 1).",
)

# 개발 중 Vite 프론트(5173)에서 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(categories.router, prefix="/api", tags=["categories"])
app.include_router(tournaments.router, prefix="/api", tags=["tournaments"])
app.include_router(matches.router, prefix="/api", tags=["matches"])
app.include_router(players.router, prefix="/api", tags=["players"])
app.include_router(misc.router, prefix="/api", tags=["misc"])


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
