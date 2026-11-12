from uuid import UUID

from app.api.cli.services.cli_presence import presence
from app.api.practice.models.practice import PracticeSession, PracticeSnapshot
from app.api.practice.models.repository import GraphEvent
from app.api.practice.schemas.git_practice import PracticeState, StoredSnapshot
from app.api.practice.services.repository_state import restore_current
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class PracticeStateService:
    @staticmethod
    async def read_practice_state(db: AsyncSession, session_id: UUID) -> PracticeState:
        """Собрать текущий снимок, курсор истории и присутствие CLI"""
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
