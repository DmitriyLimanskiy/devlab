import asyncio
from typing import Annotated
from uuid import UUID

from app.api.schemas.practice.git_practice import (
    PracticeState,
    SnapshotHistory,
    StoredSnapshot,
)
from app.db.models.practice.practice import PracticeSession, PracticeSnapshot
from app.db.models.practice.repository import GraphEvent, RepositoryCommit
from app.db.session import get_session, get_session_factory
from app.services.cli.cli_presence import presence
from app.services.practice.practice_events import events
from app.services.practice.repository_state import restore_current
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1", tags=["practice"])
ws_router = APIRouter(prefix="/ws", tags=["practice"])


@router.get("/practice-sessions/{session_id}/snapshot", response_model=PracticeState)
async def get_practice_state(
    session_id: UUID,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    # Один SELECT: метаданные сессии и снимок видны в одном состоянии БД
    row = (
        await db.execute(
            select(
                PracticeSession,
                PracticeSnapshot,
                select(func.max(GraphEvent.id))
                .where(GraphEvent.session_id == session_id)
                .scalar_subquery(),
            )
            .outerjoin(
                PracticeSnapshot, PracticeSnapshot.session_id == PracticeSession.id
            )
            .where(PracticeSession.id == session_id)
            .order_by(
                PracticeSnapshot.generation.desc(), PracticeSnapshot.version.desc()
            )
            .limit(1)
        )
    ).first()
    if row is None:
        raise HTTPException(404, "Сессия не найдена")
    session, snapshot, history_id = row
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
        snapshot=StoredSnapshot.model_validate(await restore_current(db, snapshot))
        if snapshot
        else None,
        graph_history_id=history_id or 0,
    )


@router.get("/practice-sessions/{session_id}/snapshots", response_model=SnapshotHistory)
async def get_snapshot_history(
    session_id: UUID,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
    after_id: int = Query(default=0, ge=0),
    through_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=100, ge=1, le=200),
):
    if await db.get(PracticeSession, session_id) is None:
        raise HTTPException(404, "Сессия не найдена")
    query = select(GraphEvent).where(GraphEvent.session_id == session_id)
    if through_id is not None:
        query = query.where(GraphEvent.id <= through_id)
    # Предыдущие изменения refs нужны для восстановления начала страницы
    events_before = (
        await db.scalars(query.where(GraphEvent.id <= after_id).order_by(GraphEvent.id))
    ).all()
    rows = list(
        (
            await db.scalars(
                query.where(GraphEvent.id > after_id)
                .order_by(GraphEvent.id)
                .limit(limit + 1)
            )
        ).all()
    )
    page = rows[:limit]
    commits = (
        (
            await db.scalars(
                select(RepositoryCommit)
                .where(
                    RepositoryCommit.session_id == session_id,
                    RepositoryCommit.first_event_id.in_([row.id for row in page]),
                )
                .order_by(RepositoryCommit.sha)
            )
        ).all()
        if page
        else []
    )
    refs, targets, repository_id = {}, {}, None
    snapshots = []
    for event in [*events_before, *page]:
        if event.repository_id != repository_id:
            refs, targets = {}, {}
            repository_id = event.repository_id
        for name, change in event.ref_changes.items():
            if change["after"] is None:
                refs.pop(name, None)
                targets.pop(name, None)
            else:
                refs[name] = change["after"]
                if change["commit"] is None:
                    targets.pop(name, None)
                else:
                    targets[name] = change["commit"]
        if event.id <= after_id:
            continue
        state = dict(event.context)
        if state["kind"] == "repository":
            state.update(
                refs=[f"{name} {sha}" for name, sha in sorted(refs.items())],
                ref_commits=dict(targets),
                files=[],
                operations=[],
                commits=[
                    {"id": commit.sha, "parents": commit.parents}
                    for commit in commits
                    if commit.first_event_id == event.id
                ],
            )
        snapshots.append(
            StoredSnapshot(
                id=event.id,
                session_id=session_id,
                schema_version=1,
                generation=event.generation,
                version=event.version,
                state=state,
                received_at=event.received_at,
            )
        )
    response.headers["Cache-Control"] = "no-store"
    return SnapshotHistory(snapshots=snapshots, has_more=len(rows) > limit)


@ws_router.websocket("/practice-sessions/{session_id}")
async def practice_events(websocket: WebSocket, session_id: UUID):
    # Проверка короткой сессией: не удерживать соединение БД весь срок WebSocket
    async with get_session_factory()() as db:
        exists = await db.get(PracticeSession, session_id)
    if exists is None:
        await websocket.close(code=1008)
        return
    await stream_events(websocket, session_id, events)


async def stream_events(websocket, session_id, bus):
    await websocket.accept()
    with bus.subscribe(session_id) as queue:
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
