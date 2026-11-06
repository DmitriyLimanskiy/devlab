from typing import Annotated

from app.api.routes.cli.cli import authorized_session, bearer
from app.api.schemas.cli.worktree import WorktreeAck, WorktreeReq
from app.db.session import get_session_factory
from app.services.cli.live_worktree import live_worktree
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError

router = APIRouter(prefix="/api/v1", tags=["worktree"])
ws_router = APIRouter(prefix="/ws", tags=["cli"])


@router.post("/cli-worktree", response_model=WorktreeAck)
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


@ws_router.websocket("/cli-worktree")
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
