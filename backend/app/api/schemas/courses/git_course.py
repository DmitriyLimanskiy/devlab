from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GitCourseReq(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course_slug: str = Field(min_length=1, max_length=100, pattern=r"^git-.+$")


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
