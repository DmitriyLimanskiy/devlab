import os
import unittest
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from app.db.config import database_url
from sqlalchemy import MetaData, Table, select, text, func
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.schema import CreateSchema, DropSchema
from sqlalchemy.pool import NullPool


@unittest.skipUnless(os.environ.get("RUN_DB_TESTS") == "1", "Нужен PostgreSQL")
class GraphMigrationTest(unittest.IsolatedAsyncioTestCase):
    async def test_backfill_and_fresh_delivery(self):
        schema = "test_graph_migration_" + uuid4().hex
        engine = create_async_engine(
            os.environ.get("TEST_DATABASE_URL") or database_url(), poolclass=NullPool
        )
        try:
            async with engine.begin() as connection:
                await connection.execute(CreateSchema(schema))
                await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))

                def migrate(sync):
                    config = Config(
                        str(Path(__file__).resolve().parents[1] / "alembic.ini")
                    )
                    config.attributes["connection"] = sync
                    command.upgrade(config, "20261106_0002")
                    metadata = MetaData()
                    courses = Table("courses", metadata, autoload_with=sync)
                    sessions = Table("practice_sessions", metadata, autoload_with=sync)
                    snapshots = Table(
                        "practice_snapshots", metadata, autoload_with=sync
                    )
                    course_id = sync.execute(
                        courses.insert()
                        .values(slug="git", title="Git")
                        .returning(courses.c.id)
                    ).scalar_one()
                    sid = uuid4()
                    sync.execute(
                        sessions.insert().values(
                            id=sid, course_id=course_id, generation=1
                        )
                    )
                    sha = "a" * 40
                    state = dict(
                        kind="repository",
                        path="/repo",
                        head=sha,
                        branch="main",
                        head_kind="branch",
                        commits=[dict(id=sha, parents=[])],
                        refs=[f"refs/heads/main {sha}", f"refs/heads/dev {sha}"],
                        ref_commits={"refs/heads/main": sha, "refs/heads/dev": sha},
                        files=[],
                        operations=[],
                        history_limit=200,
                        history_boundary=[],
                        history_truncated=False,
                        is_shallow=False,
                    )
                    sync.execute(
                        snapshots.insert().values(
                            session_id=sid,
                            schema_version=1,
                            generation=1,
                            version=1,
                            state=state,
                        )
                    )
                    state = {**state, "branch": "dev"}
                    sync.execute(
                        snapshots.insert().values(
                            session_id=sid,
                            schema_version=1,
                            generation=1,
                            version=2,
                            state=state,
                        )
                    )
                    command.upgrade(config, "20261106_0003")
                    metadata = MetaData()
                    tables = {
                        name: Table(name, metadata, autoload_with=sync)
                        for name in (
                            "practice_snapshots",
                            "practice_current_states",
                            "practice_snapshot_receipts",
                            "repository_commits",
                            "practice_graph_events",
                        )
                    }
                    for name, expected in (
                        ("practice_snapshots", 2),
                        ("practice_current_states", 1),
                        ("practice_snapshot_receipts", 2),
                        ("repository_commits", 1),
                        ("practice_graph_events", 1),
                    ):
                        self.assertEqual(
                            sync.scalar(select(func.count()).select_from(tables[name])),
                            expected,
                        )
                    current = (
                        sync.execute(select(tables["practice_current_states"]))
                        .mappings()
                        .one()
                    )
                    self.assertEqual(current["state"]["branch"], "dev")
                    self.assertNotIn("commits", current["state"])
                    receipt = tables["practice_snapshot_receipts"]
                    next_id = sync.execute(
                        receipt.insert()
                        .values(
                            session_id=sid, generation=1, version=3, digest="b" * 64
                        )
                        .returning(receipt.c.id)
                    ).scalar_one()
                    self.assertGreater(next_id, current["id"])
                    command.upgrade(config, "head")
                    self.assertIsNone(
                        sync.execute(
                            text("SELECT to_regclass('practice_snapshots')")
                        ).scalar_one()
                    )
                    self.assertEqual(
                        sync.scalar(
                            select(func.count()).select_from(
                                tables["repository_commits"]
                            )
                        ),
                        1,
                    )

                await connection.run_sync(migrate)
        finally:
            async with engine.begin() as connection:
                await connection.execute(
                    DropSchema(schema, cascade=True, if_exists=True)
                )
            await engine.dispose()
