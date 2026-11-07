from typing import Annotated
from uuid import UUID

from app.api.schemas.practice.git_practice import PracticeState, SnapshotHistory
from app.db.models.practice.practice import PracticeSession
from app.db.session import get_session, get_session_factory
from app.services.practice.event_stream import EventStream
from app.services.practice.graph_history import GraphHistoryService
from app.services.practice.practice_events import events
from app.services.practice.practice_state import PracticeStateService
from fastapi import APIRouter, Depends, Query, Response, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1", tags=["practice"])
ws_router = APIRouter(prefix="/ws", tags=["practice"])


@router.get("/practice-sessions/{session_id}/snapshot", response_model=PracticeState)
async def get_practice_state(
    session_id: UUID,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """Вернуть текущее состояние практики без кеширования HTTP-ответа"""
    state = await PracticeStateService.read_practice_state(db, session_id)
    response.headers["Cache-Control"] = "no-store"
    return state


@router.get("/practice-sessions/{session_id}/snapshots", response_model=SnapshotHistory)
async def get_snapshot_history(
    session_id: UUID,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
    after_id: int = Query(default=0, ge=0),
    through_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=100, ge=1, le=200),
):
    """Вернуть страницу истории графа с проверенными параметрами запроса"""
    history = await GraphHistoryService.read_snapshot_history(
        db, session_id, after_id=after_id, through_id=through_id, limit=limit
    )
    response.headers["Cache-Control"] = "no-store"
    return history


@ws_router.websocket("/practice-sessions/{session_id}")
async def practice_events(websocket: WebSocket, session_id: UUID):
    """Проверить сессию и открыть поток событий графа для браузера"""
    # Проверка короткой сессией: не удерживать соединение БД весь срок WebSocket
    async with get_session_factory()() as db:
        exists = await db.get(PracticeSession, session_id)
    if exists is None:
        await websocket.close(code=1008)
        return
    await EventStream.stream_events(websocket, session_id, events)
