from typing import Annotated, Literal
from uuid import UUID

from app.api.schemas.practice.git_state import (
    FileState,
    NoRepositoryState,
    UnavailableState,
)
from pydantic import BaseModel, ConfigDict, Field


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
