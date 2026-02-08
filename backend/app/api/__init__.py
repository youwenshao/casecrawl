"""
API routes package.
"""
from fastapi import APIRouter

from app.api import batches, cases, sessions, websocket

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(batches.router)
api_router.include_router(cases.router)
api_router.include_router(sessions.router)

# WebSocket routes (no prefix)
ws_router = APIRouter()
ws_router.include_router(websocket.router)
