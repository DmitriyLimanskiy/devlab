"""Доставка оперативных файлов и индекса отдельно от истории графа"""

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Response,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
)
from fastapi.security import HTTPAuthorizationCredentials

from app.api.routes.practice import stream_events
from app.api.routes.cli import authorized_session, bearer
from app.api.schemas.worktree import WorktreeReq, WorktreeRes, WorktreeAck
from app.db.session import get_session_factory
from app.services.live_worktree import live_worktree
from pydantic import ValidationError

router = APIRouter(tags=["worktree"])


@router.post("/api/v1/cli-worktree", response_model=WorktreeAck)
async def cli_worktree(
    request: WorktreeReq,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    await authorize_worktree(request, credentials)
    return live_worktree.publish(request)


async def authorize_worktree(request, credentials):
    if not live_worktree.authorize(request.session_id, request.generation, credentials):
        # После перезапуска backend восстанавливаем допуск по прежнему ключу
        async with get_session_factory()() as db:
            session = await authorized_session(
                db, request.session_id, request.generation, credentials
            )
            generation, key_hash = session.generation, session.key_hash
            await db.commit()
        live_worktree.bind(request.session_id, generation, key_hash)
        live_worktree.authorize(request.session_id, request.generation, credentials)


@router.get(
    "/api/v1/practice-sessions/{session_id}/worktree", response_model=WorktreeRes
)
async def get_worktree(session_id: UUID, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return live_worktree.read(session_id)


@router.websocket("/ws/practice-sessions/{session_id}/worktree")
async def worktree_events(websocket: WebSocket, session_id: UUID):
    await stream_events(websocket, session_id, live_worktree.events)


@router.websocket("/ws/cli-worktree")
async def receive_cli_worktree(websocket: WebSocket):
    header = websocket.headers.get("authorization", "")
    scheme, _, key = header.partition(" ")
    credentials = (
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=key)
        if scheme.lower() == "bearer" and key
        else None
    )
    await websocket.accept()
    try:
        while True:
            try:
                request = WorktreeReq.model_validate(await websocket.receive_json())
                await authorize_worktree(request, credentials)
                live_worktree.publish(request)
            except (ValidationError, ValueError):
                await websocket.send_json({"type": "error", "status": 422})
                await websocket.close(code=1008)
                return
            except HTTPException as error:
                await websocket.send_json(
                    {"type": "error", "status": error.status_code}
                )
                await websocket.close(code=1008)
                return
            await websocket.send_json(
                {
                    "type": "ack",
                    **WorktreeAck.model_validate(request.model_dump()).model_dump(
                        mode="json"
                    ),
                }
            )
    except WebSocketDisconnect:
        pass
