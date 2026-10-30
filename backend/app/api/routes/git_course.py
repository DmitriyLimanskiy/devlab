from typing import Annotated

from app.api.schemas.git_course import GitCourseRes
from app.db.models.course import Course, CourseStep
from app.db.models.practice import PracticeSession
from app.db.session import get_session
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1", tags=["git-course"])


@router.post("/git-course", response_model=GitCourseRes)
async def git_course(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> GitCourseRes:
    course = await db.scalar(select(Course).where(Course.slug == "git"))

    if course is None:
        raise HTTPException(status_code=404, detail="Курс Git не найден")

    # Создать сессию или получить существующую
    statement = insert(PracticeSession).values(
        course_id=course.id,
        status="active",
        generation=0,
    )

    statement = statement.on_conflict_do_update(
        index_elements=[PracticeSession.course_id],
        index_where=PracticeSession.status == "active",
        set_={"course_id": statement.excluded.course_id},
    ).returning(PracticeSession)

    practice_session = await db.scalar(statement)
    await db.commit()

    # Далее — получение шагов и формирование ответа
    steps = await db.scalars(
        select(CourseStep)
        .where(CourseStep.course_id == course.id)
        .order_by(CourseStep.position, CourseStep.id)
    )

    return GitCourseRes(
        session_id=practice_session.id,
        generation=practice_session.generation,
        steps=steps.all(),
    )
