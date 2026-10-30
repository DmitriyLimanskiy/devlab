"""Проверки ручки Git в изолированных временных схемах PostgreSQL"""

import asyncio
import os
import unittest
from uuid import uuid4

from app.api.routes.git_course import git_course
from app.db.base import Base
from app.db.config import database_url
from app.db.models import Course, CourseStep, PracticeSession
from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.schema import CreateSchema, DropSchema


@unittest.skipUnless(
    os.environ.get("RUN_DB_TESTS") == "1", "Нужен RUN_DB_TESTS=1 и PostgreSQL"
)
class GitCourseTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.schema = "test_git_course_" + uuid4().hex
        self.engine = create_async_engine(
            os.environ.get("TEST_DATABASE_URL") or database_url(), poolclass=NullPool
        )
        async with self.engine.begin() as connection:
            await connection.execute(CreateSchema(self.schema))
        translated = self.engine.execution_options(
            schema_translate_map={None: self.schema}
        )
        async with translated.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.factory = async_sessionmaker(translated, expire_on_commit=False)

    async def asyncTearDown(self):
        async with self.engine.begin() as connection:
            await connection.execute(DropSchema(self.schema, cascade=True))
        await self.engine.dispose()

    async def prepare_courses(self):
        async with self.factory() as db:
            git, other = (
                Course(slug="git", title="Git"),
                Course(slug="python", title="Python"),
            )
            db.add_all([git, other])
            await db.flush()
            db.add_all(
                [
                    CourseStep(
                        course_id=git.id,
                        slug="second",
                        position=2,
                        title="Второй",
                        content={},
                    ),
                    CourseStep(
                        course_id=git.id,
                        slug="first",
                        position=1,
                        title="Первый",
                        content={},
                    ),
                    CourseStep(
                        course_id=other.id,
                        slug="other",
                        position=1,
                        title="Другой курс",
                        content={},
                    ),
                ]
            )
            await db.commit()

    async def request(self):
        async with self.factory() as db:
            return await git_course(db)

    async def test_parallel_opening_and_steps(self):
        await self.prepare_courses()
        results = await asyncio.gather(*(self.request() for _ in range(6)))
        self.assertEqual(len({r.session_id for r in results}), 1)
        self.assertEqual([s.slug for s in results[0].steps], ["first", "second"])
        self.assertEqual(results[0].generation, 0)
        async with self.factory() as db:
            self.assertEqual(
                await db.scalar(select(func.count()).select_from(PracticeSession)), 1
            )
            await db.execute(
                update(PracticeSession).values(
                    generation=2, key_hash="test", connected_at=func.now()
                )
            )
            await db.commit()
        reused = await self.request()
        self.assertEqual(reused.session_id, results[0].session_id)
        self.assertEqual(reused.generation, 2)
        self.assertNotIn("key_hash", reused.model_dump())

    async def test_closed_session(self):
        await self.prepare_courses()
        old = await self.request()
        async with self.factory() as db:
            await db.execute(
                update(PracticeSession).values(status="closed", closed_at=func.now())
            )
            await db.commit()
        self.assertNotEqual(old.session_id, (await self.request()).session_id)

    async def test_missing_course(self):
        with self.assertRaises(HTTPException) as error:
            await self.request()
        self.assertEqual(error.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
