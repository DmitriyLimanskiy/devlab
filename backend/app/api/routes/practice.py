import asyncio
from typing import Annotated
from uuid import UUID

from app.api.schemas.practice import PracticeState, StoredSnapshot
from app.db.models.practice import PracticeSession, PracticeSnapshot
from app.db.session import get_session, get_session_factory
from app.services.cli_presence import presence
from app.services.practice_events import events
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["practice"])


@router.get(
    "/api/v1/practice-sessions/{session_id}/snapshot", response_model=PracticeState
)
async def get_practice_state(
    session_id: UUID,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    # Один SELECT: метаданные сессии и снимок видны в одном состоянии БД
    row = (
        await db.execute(
            select(PracticeSession, PracticeSnapshot)
            .outerjoin(
                PracticeSnapshot, PracticeSnapshot.session_id == PracticeSession.id
            )
            .where(PracticeSession.id == session_id)
        )
    ).first()
    if row is None:
        raise HTTPException(404, "Сессия не найдена")
    session, snapshot = row
    response.headers["Cache-Control"] = "no-store"
    lease = (
        presence.remaining(session.id, session.generation)
        if session.status == "active"
        else 0.0
    )
    return PracticeState(
        cli_connected=lease > 0,
        cli_lease_seconds=lease,
        session_id=session.id,
        status=session.status,
        generation=session.generation,
        connected_at=session.connected_at,
        snapshot=StoredSnapshot.model_validate(snapshot) if snapshot else None,
    )


@router.websocket("/ws/practice-sessions/{session_id}")
async def practice_events(websocket: WebSocket, session_id: UUID):
    # Проверка короткой сессией: не удерживать соединение БД весь срок WebSocket
    async with get_session_factory()() as db:
        exists = await db.get(PracticeSession, session_id)
    if exists is None:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    with events.subscribe(session_id) as queue:
        # ready отправляется после регистрации, затем браузер читает HTTP-снимок
        await websocket.send_json({"type": "ready"})
        receiver = asyncio.create_task(websocket.receive_text())
        pending = None
        try:
            while True:
                pending = asyncio.create_task(queue.get())
                done, _ = await asyncio.wait(
                    {receiver, pending}, timeout=20, return_when=asyncio.FIRST_COMPLETED
                )
                if receiver in done:
                    receiver.result()
                    receiver = asyncio.create_task(websocket.receive_text())
                if pending in done:
                    await websocket.send_json(pending.result())
                else:
                    pending.cancel()
                    await asyncio.gather(pending, return_exceptions=True)
                if not done:
                    await websocket.send_json({"type": "ping"})
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            receiver.cancel()
            if pending is not None:
                pending.cancel()
            await asyncio.gather(
                receiver, *([pending] if pending else []), return_exceptions=True
            )
