import hashlib
import secrets

from app.db.models.practice.practice import PracticeSession
from app.db.session import get_session_factory
from app.services.cli.live_worktree import live_worktree
from fastapi import HTTPException
from sqlalchemy import select


class CliAuthorization:
    @staticmethod
    async def authorized_session(db, session_id, generation, credentials):
        """Проверить ключ, статус и поколение с блокировкой записи сессии"""
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

    @staticmethod
    async def authorize_worktree(request, credentials):
        """Проверить допуск оперативного канала и восстановить его из БД при необходимости"""
        if not live_worktree.authorize(
            request.session_id, request.generation, credentials
        ):
            # После перезапуска backend восстанавливаем допуск по прежнему ключу
            async with get_session_factory()() as db:
                session = await CliAuthorization.authorized_session(
                    db, request.session_id, request.generation, credentials
                )
                generation, key_hash = session.generation, session.key_hash
                await db.commit()
            live_worktree.bind(request.session_id, generation, key_hash)
            live_worktree.authorize(request.session_id, request.generation, credentials)
