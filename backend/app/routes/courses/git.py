from typing import Annotated

from app.db.session import get_session
from app.models.courses.git import GitCourseRes
from app.schemas.courses import Course, CourseStep
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1", tags=["git-course"])


@router.get("/git-course", response_model=GitCourseRes)
async def git_course(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> GitCourseRes:
    steps = await db.scalars(
        select(CourseStep)
        .join(Course, CourseStep.course_id == Course.id)
        .where(Course.slug == "git")
        .order_by(CourseStep.position, CourseStep.id)
    )

    return GitCourseRes(steps=steps.all())
