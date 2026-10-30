from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .state import GitState


class SnapshotReq(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    session_id: UUID
    generation: int = Field(gt=0, strict=True)
    version: int = Field(gt=0, strict=True)
    state: GitState
