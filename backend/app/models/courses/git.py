"""Модели HTTP-ответа с шагами курса Git."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CourseStepRes(BaseModel):
    """Шаг курса; поддерживает преобразование из SQLAlchemy-объекта"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    slug: str
    position: int = Field(gt=0)
    title: str
    content: dict[str, Any]


class GitCourseRes(BaseModel):
    steps: list[CourseStepRes]
