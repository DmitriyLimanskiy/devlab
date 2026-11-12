import asyncio
import os
import unittest
from uuid import uuid4

from app.api.courses.routers.git_course import git_course, git_courses
from app.api.courses.schemas.git_course import GitCourseReq
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
        """Создать изолированную схему БД и фабрику тестовых сессий"""
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
        """Удалить тестовую схему БД и освободить подключения"""
        async with self.engine.begin() as connection:
            await connection.execute(DropSchema(self.schema, cascade=True))
        await self.engine.dispose()

    async def prepare_courses(self):
        """Создать тестовые курсы и шаги в изолированной схеме БД"""
        async with self.factory() as db:
            git, other = (
                Course(slug="git-sandbox", title="Git"),
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
        """Открыть тестовую сессию курса"""
        async with self.factory() as db:
            return await git_course(db, GitCourseReq(course_slug="git-sandbox"))

    async def test_parallel_opening_and_steps(self):
        """Проверить совместное открытие одной сессии и порядок шагов курса"""
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
        """Проверить создание новой сессии после закрытия предыдущей"""
        await self.prepare_courses()
        old = await self.request()
        async with self.factory() as db:
            await db.execute(
                update(PracticeSession).values(status="closed", closed_at=func.now())
            )
            await db.commit()
        self.assertNotEqual(old.session_id, (await self.request()).session_id)

    async def test_missing_course(self):
        """Проверить ответ при отсутствии запрошенного курса"""
        with self.assertRaises(HTTPException) as error:
            await self.request()
        self.assertEqual(error.exception.status_code, 404)


class GitCourseTabsTest(GitCourseTest):
    async def test_course_slug_is_not_limited_to_two_names(self):
        """Проверить открытие произвольного допустимого Git-курса"""
        async with self.factory() as db:
            db.add(Course(slug="git-advanced", title="Новый курс", position=3))
            await db.commit()
            courses = await git_courses(db)
            self.assertEqual([course.id for course in courses], ["git-advanced"])
            self.assertEqual(courses[0].title, "Новый курс")
            practice = await git_course(db, GitCourseReq(course_slug=courses[0].id))
            self.assertEqual(practice.steps, [])
            session = await db.get(PracticeSession, practice.session_id)
            stored_course = await db.get(Course, session.course_id)
            self.assertEqual(stored_course.slug, "git-advanced")

    async def test_list_filters_courses_without_creating_sessions(self):
        """Проверить фильтрацию списка Git-курсов без создания сессий"""
        await self.prepare_courses()
        async with self.factory() as db:
            db.add(
                Course(slug="git-full-course", title="Git — полный курс", position=2)
            )
            await db.commit()
            courses = await git_courses(db)
            self.assertEqual(
                [course.id for course in courses], ["git-sandbox", "git-full-course"]
            )
            self.assertEqual(
                await db.scalar(select(func.count()).select_from(PracticeSession)), 0
            )

    async def test_empty_list(self):
        """Проверить пустой список при отсутствии Git-курсов"""
        async with self.factory() as db:
            self.assertEqual(await git_courses(db), [])

    async def test_independent_sessions_and_empty_full_course_steps(self):
        """Проверить независимость сессий курсов и пустых списков шагов"""
        await self.prepare_courses()
        sandbox = await self.request()
        async with self.factory() as db:
            db.add(
                Course(slug="git-full-course", title="Git — полный курс", position=2)
            )
            await db.commit()
            full = await git_course(db, GitCourseReq(course_slug="git-full-course"))
            self.assertNotEqual(full.session_id, sandbox.session_id)
            self.assertEqual(full.steps, [])
            self.assertEqual(
                (
                    await git_course(db, GitCourseReq(course_slug="git-full-course"))
                ).session_id,
                full.session_id,
            )
            self.assertEqual(
                (
                    await git_course(db, GitCourseReq(course_slug="git-sandbox"))
                ).session_id,
                sandbox.session_id,
            )
            self.assertEqual(
                await db.scalar(select(func.count()).select_from(PracticeSession)), 2
            )

    async def test_missing_full_course_does_not_replace_sandbox(self):
        """Проверить отсутствие подмены недоступного курса песочницей"""
        await self.prepare_courses()
        sandbox = await self.request()
        async with self.factory() as db:
            with self.assertRaises(HTTPException) as error:
                await git_course(db, GitCourseReq(course_slug="git-full-course"))
            self.assertEqual(error.exception.status_code, 404)
        self.assertEqual((await self.request()).session_id, sandbox.session_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
