"""Нормализованные коммиты, события refs и подтверждения доставки"""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.db.base import Base
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column


class GraphEvent(Base):
    __tablename__ = "practice_graph_events"
    __table_args__ = (Index("ix_graph_events_session_id", "session_id", "id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="RESTRICT")
    )
    repository_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    generation: Mapped[int] = mapped_column(BigInteger)
    version: Mapped[int] = mapped_column(BigInteger)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB)
    ref_changes: Mapped[dict[str, Any]] = mapped_column(JSONB)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RepositoryCommit(Base):
    __tablename__ = "repository_commits"

    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="RESTRICT"), primary_key=True
    )
    repository_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    sha: Mapped[str] = mapped_column(String(64), primary_key=True)
    parents: Mapped[list[str]] = mapped_column(JSONB)
    first_event_id: Mapped[int] = mapped_column(
        ForeignKey("practice_graph_events.id", ondelete="RESTRICT"), index=True
    )


class SnapshotReceipt(Base):
    __tablename__ = "practice_snapshot_receipts"
    __table_args__ = (
        UniqueConstraint(
            "session_id", "generation", "version", name="uq_snapshot_receipt_delivery"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="RESTRICT")
    )
    generation: Mapped[int] = mapped_column(BigInteger)
    version: Mapped[int] = mapped_column(BigInteger)
    digest: Mapped[str] = mapped_column(String(64))
