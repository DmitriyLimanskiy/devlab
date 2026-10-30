import hashlib
import secrets
from datetime import UTC, datetime
from typing import Annotated

from app.api.schemas.cli import CliConnectReq, CliConnectRes
from app.api.schemas.snapshot import SnapshotReq, SnapshotRes
from app.db.models.course import Course
from app.db.models.practice import PracticeSession, PracticeSnapshot
from app.db.session import get_session
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
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Требуется ключ подключения",
            headers={"WWW-Authenticate": "Bearer"},
        )

    practice_session = await db.scalar(
        select(PracticeSession)
        .where(PracticeSession.id == snapshot.session_id)
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

    if practice_session.generation != snapshot.generation:
        raise HTTPException(
            status_code=409,
            detail="Поколение подключения больше не действует",
        )

    saved = await db.get(PracticeSnapshot, snapshot.session_id)
    state = snapshot.state.model_dump(mode="json")
    duplicate = False

    if saved is not None:
        if saved.generation > snapshot.generation:
            raise HTTPException(
                status_code=409,
                detail="Сохранён снимок более нового поколения",
            )

        if saved.generation == snapshot.generation:
            if saved.version > snapshot.version:
                raise HTTPException(
                    status_code=409,
                    detail="Версия снимка устарела",
                )

            if saved.version == snapshot.version:
                if (
                    saved.schema_version != snapshot.schema_version
                    or saved.state != state
                ):
                    raise HTTPException(
                        status_code=409,
                        detail="Эта версия уже сохранена с другим содержимым",
                    )

                duplicate = True

    if not duplicate:
        if saved is None:
            saved = PracticeSnapshot(session_id=snapshot.session_id)
            db.add(saved)

        saved.schema_version = snapshot.schema_version
        saved.generation = snapshot.generation
        saved.version = snapshot.version
        saved.state = state
        saved.received_at = datetime.now(UTC)

    await db.commit()

    return SnapshotRes(
        session_id=snapshot.session_id,
        generation=snapshot.generation,
        version=snapshot.version,
    )
