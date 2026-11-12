import subprocess
import tempfile
from pathlib import Path

import test_git_course
from app.api.cli.routers.cli import cli_connect, cli_send_state
from app.api.cli.schemas.cli import CliConnectReq
from app.api.cli.schemas.snapshot import SnapshotReq
from app.api.practice.models.practice import PracticeSnapshot
from app.api.practice.models.repository import (
    GraphEvent,
    RepositoryCommit,
    SnapshotReceipt,
)
from app.api.practice.routers.git_practice import (
    get_practice_state,
    get_snapshot_history,
)
from fastapi import Response
from fastapi.security import HTTPAuthorizationCredentials
from git_snapshot_fixture import read_state
from sqlalchemy import func, select


class NormalizedRepositoryTest(test_git_course.GitCourseTest):
    async def test_switch_files_commit_refs_and_retries(self):
        """Проверить разделение текущего состояния, истории графа и повторных снимков"""

        await self.prepare_courses()
        course = await self.request()
        async with self.factory() as db:
            connection = await cli_connect(CliConnectReq(course_slug="git-sandbox"), db)
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=connection.key
        )
        version = 0
        bodies = []

        async def publish(folder):
            """Отправить тестовое состояние с очередной версией"""
            nonlocal version
            version += 1
            body = SnapshotReq(
                schema_version=1,
                session_id=course.session_id,
                generation=connection.generation,
                version=version,
                state=read_state(folder),
            )
            bodies.append(body)
            async with self.factory() as db:
                return await cli_send_state(body, db, credentials)

        async def counts():
            """Посчитать записи текущего состояния, коммитов, событий и подтверждений"""
            async with self.factory() as db:
                return tuple(
                    [
                        await db.scalar(select(func.count()).select_from(model))
                        for model in (
                            PracticeSnapshot,
                            RepositoryCommit,
                            GraphEvent,
                            SnapshotReceipt,
                        )
                    ]
                )

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)

            def git(*args):
                """Выполнить Git во временном тестовом репозитории"""
                return subprocess.run(
                    ["git", "-C", directory, *args], check=True, capture_output=True
                )

            git("init", "-b", "main")
            git("config", "user.name", "Test")
            git("config", "user.email", "test@example.invalid")
            (folder / "file").write_text("base")
            git("add", ".")
            git("commit", "-m", "base")
            await publish(folder)
            self.assertEqual(await counts(), (1, 1, 1, 1))
            git("branch", "dev")
            await publish(folder)
            self.assertEqual(await counts(), (1, 1, 2, 2))
            git("switch", "dev")
            await publish(folder)
            self.assertEqual(await counts(), (1, 1, 2, 3))
            (folder / "file").write_text("edit")
            await publish(folder)
            self.assertEqual(await counts(), (1, 1, 2, 4))
            git("add", ".")
            await publish(folder)
            self.assertEqual(await counts(), (1, 1, 2, 5))
            git("commit", "-m", "dev")
            await publish(folder)
            self.assertEqual(await counts(), (1, 2, 3, 6))
            git("switch", "main")
            await publish(folder)
            self.assertEqual(await counts(), (1, 2, 3, 7))
            git("merge", "dev")
            await publish(folder)
            self.assertEqual(await counts(), (1, 2, 4, 8))
            git("branch", "-d", "dev")
            await publish(folder)
            self.assertEqual(await counts(), (1, 2, 5, 9))
            async with self.factory() as db:
                latest = await get_practice_state(course.session_id, Response(), db)
                self.assertEqual(
                    latest.snapshot.state.model_dump(mode="json"),
                    bodies[-1].state.model_dump(mode="json"),
                )
                history = await get_snapshot_history(
                    course.session_id,
                    Response(),
                    db,
                    after_id=0,
                    through_id=latest.graph_history_id,
                    limit=2,
                )
                self.assertTrue(history.has_more)
                self.assertEqual([s.version for s in history.snapshots], [1, 2])
                cursor = history.snapshots[-1].id
                page = await get_snapshot_history(
                    course.session_id,
                    Response(),
                    db,
                    after_id=cursor,
                    through_id=latest.graph_history_id,
                    limit=200,
                )
                self.assertEqual([s.version for s in page.snapshots], [6, 8, 9])
                self.assertEqual(
                    sum(
                        len(s.state.commits)
                        for s in [*history.snapshots, *page.snapshots]
                    ),
                    2,
                )
                self.assertFalse(
                    any(
                        ref.startswith("refs/heads/dev ")
                        for ref in page.snapshots[-1].state.refs
                    )
                )
            async with self.factory() as db:
                await cli_send_state(bodies[0], db, credentials)
            self.assertEqual(await counts(), (1, 2, 5, 9))
