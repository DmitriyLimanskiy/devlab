from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CourseStepRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    slug: str
    position: int = Field(gt=0)
    title: str
    content: dict[str, Any]


class GitCourseRes(BaseModel):
    session_id: UUID
    generation: int
    steps: list[CourseStepRes]
