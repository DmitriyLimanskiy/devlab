from uuid import UUID

from pydantic import BaseModel


class CliConnectReq(BaseModel):
    course_slug: str


class CliConnectRes(BaseModel):
    session_id: UUID
    generation: int
    key: str
