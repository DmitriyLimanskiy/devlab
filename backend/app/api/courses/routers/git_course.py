from typing import Annotated

from app.api.auth.dependencies import get_current_user
from app.api.catalog.schemas import CatalogRes
from app.api.courses.models.course import Course
from app.db.session import get_session
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1", tags=["git-course"])


@router.get(
    "/git-course",
    dependencies=[Depends(get_current_user)],
    response_model=list[CatalogRes],
)
async def git_courses(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[CatalogRes]:
    """Получить список Git-курсов без создания практических сессий"""
    courses = await db.scalars(
        select(Course)
        .where(Course.slug.startswith("git-"))
        .order_by(Course.position, Course.id)
    )
    return [
        CatalogRes(
            id=course.slug,
            title=course.title,
            description=course.description,
            status=course.status,
            position=course.position,
        )
        for course in courses.all()
    ]
