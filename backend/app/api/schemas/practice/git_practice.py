from datetime import datetime
from typing import Literal
from uuid import UUID

from app.api.schemas.cli.snapshot import SnapshotReq
from pydantic import BaseModel, ConfigDict


class StoredSnapshot(SnapshotReq):
    model_config = ConfigDict(from_attributes=True)
    id: int
    received_at: datetime


class PracticeState(BaseModel):
    session_id: UUID
    status: Literal["active", "closed"]
    generation: int
    cli_connected: bool
    cli_lease_seconds: float
    connected_at: datetime | None
    snapshot: StoredSnapshot | None
    graph_history_id: int = 0


class SnapshotHistory(BaseModel):
    snapshots: list[StoredSnapshot]
    has_more: bool
