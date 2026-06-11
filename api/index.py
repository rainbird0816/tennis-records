"""Vercel Python 서버리스 진입점.

기존 FastAPI 앱(backend/app/main.py 의 `app`)을 그대로 노출한다.
vercel.json 의 rewrite 가 `/api/*` 요청을 이 함수로 보내면 FastAPI 가 라우팅한다.
DB(tennis.db)는 functions.includeFiles 로 번들되며 읽기 전용으로 열린다.
"""
import os
import sys

_HERE = os.path.dirname(__file__)
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))

# backend 패키지(app.*) 임포트 경로 + DB 경로 지정
sys.path.insert(0, os.path.join(_ROOT, "backend"))
os.environ.setdefault("TENNIS_DB", os.path.join(_ROOT, "data", "tennis.db"))

from app.main import app  # noqa: E402  (Vercel @vercel/python 이 ASGI `app` 을 서빙)

__all__ = ["app"]
