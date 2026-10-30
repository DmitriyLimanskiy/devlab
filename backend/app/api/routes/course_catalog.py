from typing import Annotated

from app.db.session import get_session
from app.api.schemas.course_catalog import CatalogRes
from app.db.models import Course
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/catalog", response_model=list[CatalogRes])
async def catalog(
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[CatalogRes]:
    courses = await db.scalars(select(Course).order_by(Course.position, Course.id))
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
