from uuid import UUID

from app.api.routes.practice.git_practice import stream_events
from app.api.schemas.cli.worktree import WorktreeRes
from app.services.cli.live_worktree import live_worktree
from fastapi import APIRouter, Response, WebSocket

router = APIRouter(prefix="/api/v1", tags=["practice"])
ws_router = APIRouter(prefix="/ws", tags=["practice"])


@router.get("/practice-sessions/{session_id}/worktree", response_model=WorktreeRes)
async def get_worktree(session_id: UUID, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return live_worktree.read(session_id)


@ws_router.websocket("/practice-sessions/{session_id}/worktree")
async def worktree_events(websocket: WebSocket, session_id: UUID):
    await stream_events(websocket, session_id, live_worktree.events)
