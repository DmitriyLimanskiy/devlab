import hashlib

from app.api.old_cli.schemas.cli import CliResetPracticeRes
from app.api.old_cli.services.authorization import CliAuthorization
from app.api.practice.models.practice import PracticeSession, PracticeSnapshot
from app.api.practice.models.repository import (
    GraphEvent,
    RepositoryCommit,
    SnapshotReceipt,
)
from fastapi import HTTPException
from sqlalchemy import delete, select


class PracticeResetService:
    @staticmethod
    async def reset(db, request, credentials):
        """Очистить практику с сохранением ключа и безопасным повтором одного сброса"""
        if credentials is None:
            await CliAuthorization.authorized_session(
                db, request.session_id, request.generation, credentials
            )
        session = await db.scalar(
            select(PracticeSession)
            .where(PracticeSession.id == request.session_id)
            .with_for_update()
        )
        if session is None:
            raise HTTPException(404, "Сессия не найдена")
        await CliAuthorization.authorized_session(
            db, session.id, session.generation, credentials
        )
        digest = hashlib.sha256(f"reset:{request.reset_id}".encode()).hexdigest()
        if session.generation == request.generation + 1:
            receipt = await db.scalar(
                select(SnapshotReceipt).where(
                    SnapshotReceipt.session_id == session.id,
                    SnapshotReceipt.generation == session.generation,
                    SnapshotReceipt.version == 0,
                )
            )
            if receipt is not None and receipt.digest == digest:
                return session, False
        if session.generation != request.generation:
            raise HTTPException(409, "Поколение подключения больше не действует")
        if session.generation == 9223372036854775807:
            raise HTTPException(409, "Исчерпаны поколения подключения")
        for model in (PracticeSnapshot, RepositoryCommit, GraphEvent, SnapshotReceipt):
            await db.execute(delete(model).where(model.session_id == session.id))
        session.generation += 1
        # Версия 0 зарезервирована для подтверждения сброса, снимки начинаются с 1
        db.add(
            SnapshotReceipt(
                session_id=session.id,
                generation=session.generation,
                version=0,
                digest=digest,
            )
        )
        return session, True

    @staticmethod
    def response(session, request):
        """Подтвердить поколение и идентификатор применённого сброса"""
        return CliResetPracticeRes(
            session_id=session.id,
            generation=session.generation,
            reset=True,
            reset_id=request.reset_id,
        )
