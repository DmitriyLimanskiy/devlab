from collections import defaultdict
from uuid import UUID

from app.api.practice.models.practice import PracticeSession
from app.api.practice.models.repository import GraphEvent, RepositoryCommit
from app.api.practice.schemas.git_practice import SnapshotHistory, StoredSnapshot
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class GraphHistoryService:
    @staticmethod
    def _apply_ref_changes(refs, targets, changes):
        """Восстановить указатели refs и цели тегов по очередному изменению"""
        for name, change in changes.items():
            if change["after"] is None:
                refs.pop(name, None)
                targets.pop(name, None)
            else:
                refs[name] = change["after"]
                if change["commit"] is None:
                    targets.pop(name, None)
                else:
                    targets[name] = change["commit"]

    @staticmethod
    async def read_snapshot_history(
        db: AsyncSession,
        session_id: UUID,
        *,
        after_id: int,
        through_id: int | None,
        limit: int,
    ) -> SnapshotHistory:
        """Собрать страницу истории графа с восстановленными refs и новыми коммитами"""
        if await db.get(PracticeSession, session_id) is None:
            raise HTTPException(404, "Сессия не найдена")
        query = select(GraphEvent).where(GraphEvent.session_id == session_id)
        if through_id is not None:
            query = query.where(GraphEvent.id <= through_id)
        # Предыдущие изменения refs нужны для восстановления начала страницы
        events_before = (
            await db.scalars(
                query.where(GraphEvent.id <= after_id).order_by(GraphEvent.id)
            )
        ).all()
        rows = list(
            (
                await db.scalars(
                    query.where(GraphEvent.id > after_id)
                    .order_by(GraphEvent.id)
                    .limit(limit + 1)
                )
            ).all()
        )
        page = rows[:limit]
        commits = (
            (
                await db.scalars(
                    select(RepositoryCommit)
                    .where(
                        RepositoryCommit.session_id == session_id,
                        RepositoryCommit.first_event_id.in_([row.id for row in page]),
                    )
                    .order_by(RepositoryCommit.sha)
                )
            ).all()
            if page
            else []
        )
        commits_by_event = defaultdict(list)
        for commit in commits:
            commits_by_event[commit.first_event_id].append(
                {"id": commit.sha, "parents": commit.parents}
            )
        refs, targets, repository_id = {}, {}, None
        snapshots = []
        for event in [*events_before, *page]:
            if event.repository_id != repository_id:
                refs, targets = {}, {}
                repository_id = event.repository_id
            GraphHistoryService._apply_ref_changes(refs, targets, event.ref_changes)
            if event.id <= after_id:
                continue
            state = dict(event.context)
            if state["kind"] == "repository":
                state.update(
                    refs=[f"{name} {sha}" for name, sha in sorted(refs.items())],
                    ref_commits=dict(targets),
                    files=[],
                    operations=[],
                    commits=commits_by_event[event.id],
                )
            snapshots.append(
                StoredSnapshot(
                    id=event.id,
                    session_id=session_id,
                    schema_version=1,
                    generation=event.generation,
                    version=event.version,
                    state=state,
                    received_at=event.received_at,
                )
            )
        return SnapshotHistory(snapshots=snapshots, has_more=len(rows) > limit)
