"""Оперативное состояние файлов без сохранения в PostgreSQL"""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .git_state import FileState, NoRepositoryState, UnavailableState


class RepositoryFiles(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    kind: Literal["repository"]
    path: str = Field(min_length=1)
    files: list[FileState]


WorktreeState = Annotated[
    RepositoryFiles | NoRepositoryState | UnavailableState, Field(discriminator="kind")
]


class WorktreeReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: UUID
    generation: int = Field(gt=0, strict=True)
    version: int = Field(gt=0, strict=True)
    state: WorktreeState


class WorktreeRes(BaseModel):
    session_id: UUID
    generation: int
    version: int
    state: WorktreeState | None


class WorktreeAck(BaseModel):
    session_id: UUID
    generation: int
    version: int
