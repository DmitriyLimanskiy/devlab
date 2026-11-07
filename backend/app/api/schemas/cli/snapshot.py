from typing import Literal
from uuid import UUID

from app.api.schemas.practice.git_state import GitState
from pydantic import BaseModel, ConfigDict, Field


class SnapshotReq(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    session_id: UUID
    generation: int = Field(gt=0, strict=True)
    version: int = Field(gt=0, strict=True)
    state: GitState


class SnapshotRes(BaseModel):
    id: int
    session_id: UUID
    generation: int
    version: int
