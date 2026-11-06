import hashlib
import secrets
from datetime import UTC, datetime
from typing import Annotated

from app.api.schemas.cli.cli import (
    CliConnectReq,
    CliConnectRes,
    CliPresenceReq,
    CliPresenceRes,
)
from app.api.schemas.cli.snapshot import SnapshotReq, SnapshotRes
from app.db.models.courses.course import Course
from app.db.models.practice.practice import PracticeSession
from app.db.session import get_session
from app.services.cli.cli_presence import presence
from app.services.cli.live_worktree import live_worktree
from app.services.practice.practice_events import events
from app.services.practice.repository_state import store_state
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1", tags=["cli"])

bearer = HTTPBearer(auto_error=False)


@router.post("/cli-connect", response_model=CliConnectRes)
async def cli_connect(
    connect: CliConnectReq, db: Annotated[AsyncSession, Depends(get_session)]
):
    practice_session = await db.scalar(
        select(PracticeSession)
        .join(Course, PracticeSession.course_id == Course.id)
        .where(
            Course.slug == connect.course_slug,
            PracticeSession.status == "active",
        )
        .with_for_update(of=PracticeSession)
    )

    if practice_session is None:
        raise HTTPException(status_code=404, detail="Запустите выбранный курс в ЛК")

    key = secrets.token_urlsafe(32)

    practice_session.generation += 1
    practice_session.key_hash = hashlib.sha256(key.encode()).hexdigest()
    practice_session.connected_at = datetime.now(UTC)

    await db.commit()
    live_worktree.bind(
        practice_session.id, practice_session.generation, practice_session.key_hash
    )
    presence.remove(practice_session.id)
    events.publish(practice_session.id)

    return CliConnectRes(
        session_id=practice_session.id,
        generation=practice_session.generation,
        key=key,
    )


@router.post("/cli-send-snapshot", response_model=SnapshotRes)
async def cli_send_state(
    snapshot: SnapshotReq,
    db: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer),
    ],
):
    await authorized_session(db, snapshot.session_id, snapshot.generation, credentials)

    receipt, changed = await store_state(db, snapshot)
    await db.commit()
    if changed:
        events.publish(snapshot.session_id)
    return SnapshotRes(
        id=receipt.id,
        session_id=snapshot.session_id,
        generation=snapshot.generation,
        version=snapshot.version,
    )


async def authorized_session(db, session_id, generation, credentials):
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Требуется ключ подключения",
            headers={"WWW-Authenticate": "Bearer"},
        )

    practice_session = await db.scalar(
        select(PracticeSession)
        .where(PracticeSession.id == session_id)
        .with_for_update()
    )

    if practice_session is None:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    supplied_hash = hashlib.sha256(credentials.credentials.encode()).hexdigest()

    if practice_session.key_hash is None or not secrets.compare_digest(
        supplied_hash,
        practice_session.key_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Неверный ключ подключения",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if practice_session.status != "active":
        raise HTTPException(status_code=409, detail="Сессия закрыта")

    if practice_session.generation != generation:
        raise HTTPException(
            status_code=409,
            detail="Поколение подключения больше не действует",
        )

    return practice_session


@router.post("/cli-heartbeat", response_model=CliPresenceRes)
async def cli_heartbeat(
    request: CliPresenceReq,
    db: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    await authorized_session(db, request.session_id, request.generation, credentials)
    await db.commit()
    if presence.touch(request.session_id, request.generation):
        events.publish(request.session_id)
    return CliPresenceRes(
        session_id=request.session_id, generation=request.generation, connected=True
    )


@router.post("/cli-disconnect", response_model=CliPresenceRes)
async def cli_disconnect(
    request: CliPresenceReq,
    db: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    await authorized_session(db, request.session_id, request.generation, credentials)
    await db.commit()
    if presence.remove(request.session_id, request.generation):
        events.publish(request.session_id)
    return CliPresenceRes(
        session_id=request.session_id, generation=request.generation, connected=False
    )
