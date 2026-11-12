from typing import Annotated

from app.api.old_cli.routers.cli import bearer
from app.api.old_cli.schemas.worktree import WorktreeAck, WorktreeReq
from app.api.old_cli.services.authorization import CliAuthorization
from app.api.old_cli.services.live_worktree import live_worktree
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
    """Принять авторизованное оперативное состояние файлов по HTTP"""
    await CliAuthorization.authorize_worktree(request, credentials)
    return live_worktree.publish(request)


@ws_router.websocket("/cli-worktree")
async def receive_cli_worktree(websocket: WebSocket):
    """Принимать состояния файлов CLI по WebSocket и подтверждать версии"""
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
                await CliAuthorization.authorize_worktree(request, credentials)
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
