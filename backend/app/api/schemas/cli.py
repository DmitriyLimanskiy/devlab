from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CliConnectReq(BaseModel):
    course_slug: str


class CliConnectRes(BaseModel):
    session_id: UUID
    generation: int
    key: str


class CliPresenceReq(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: UUID
    generation: int = Field(gt=0, le=9223372036854775807, strict=True)


class CliPresenceRes(BaseModel):
    session_id: UUID
    generation: int
    connected: bool
