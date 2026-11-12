import hashlib
import secrets
from datetime import UTC, datetime
from typing import Annotated

from app.api.cli.schemas.cli import (
    CliConnectReq,
    CliConnectRes,
    CliPresenceReq,
    CliPresenceRes,
    CliResetPracticeReq,
    CliResetPracticeRes,
)
from app.api.cli.schemas.snapshot import SnapshotReq, SnapshotRes
from app.api.cli.services.authorization import CliAuthorization
from app.api.cli.services.cli_presence import presence
from app.api.cli.services.live_worktree import live_worktree
from app.api.cli.services.practice_reset import PracticeResetService
from app.api.courses.models.course import Course
from app.api.practice.models.practice import PracticeSession
from app.api.practice.services.practice_events import events
from app.api.practice.services.repository_state import store_state
from app.db.session import get_session
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/cli", tags=["cli"])

bearer = HTTPBearer(auto_error=False)


@router.post("/connect", response_model=CliConnectRes)
async def cli_connect(
    connect: CliConnectReq, db: Annotated[AsyncSession, Depends(get_session)]
):
    """Выдать новое поколение подключения CLI и ключ активной сессии"""
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


@router.post("/send-snapshot", response_model=SnapshotRes)
async def cli_send_state(
    snapshot: SnapshotReq,
    db: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer),
    ],
):
    """Сохранить снимок CLI и подтвердить его после commit"""
    await CliAuthorization.authorized_session(
        db, snapshot.session_id, snapshot.generation, credentials
    )

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


@router.post("/heartbeat", response_model=CliPresenceRes)
async def cli_heartbeat(
    request: CliPresenceReq,
    db: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    """Продлить присутствие авторизованного CLI и вернуть подтверждение"""
    await CliAuthorization.authorized_session(
        db, request.session_id, request.generation, credentials
    )

    await db.commit()

    if presence.touch(request.session_id, request.generation):
        events.publish(request.session_id)

    return CliPresenceRes(
        session_id=request.session_id, generation=request.generation, connected=True
    )


@router.post("/disconnect", response_model=CliPresenceRes)
async def cli_disconnect(
    request: CliPresenceReq,
    db: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    """Снять присутствие CLI текущего поколения и уведомить браузер"""
    await CliAuthorization.authorized_session(
        db, request.session_id, request.generation, credentials
    )

    await db.commit()

    if presence.remove(request.session_id, request.generation):
        events.publish(request.session_id)
    return CliPresenceRes(
        session_id=request.session_id, generation=request.generation, connected=False
    )


@router.delete("/reset-practice", response_model=CliResetPracticeRes)
async def reset_practice(
    request: CliResetPracticeReq,
    db: Annotated[AsyncSession, Depends(get_session)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    """Очистить практику и вернуть новое поколение действующему CLI"""
    session, changed = await PracticeResetService.reset(db, request, credentials)
    await db.commit()
    live_worktree.bind(session.id, session.generation, session.key_hash)
    if changed:
        presence.remove(session.id)
        presence.touch(session.id, session.generation)
        events.publish(session.id)
    return PracticeResetService.response(session, request)
