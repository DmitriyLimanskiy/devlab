from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.db.base import Base
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .course import Course


class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'closed')", name="valid_status"),
        CheckConstraint("generation >= 0", name="nonnegative_generation"),
        CheckConstraint(
            "(status = 'active' AND closed_at IS NULL) OR "
            "(status = 'closed' AND closed_at IS NOT NULL)",
            name="closed_at_matches_status",
        ),
        Index(
            "uq_practice_sessions_active_course",
            "course_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), server_default=text("'active'"))
    generation: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    key_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    connected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    course: Mapped[Course] = relationship()
    snapshot: Mapped["PracticeSnapshot | None"] = relationship(
        back_populates="session",
        passive_deletes="all",
    )


class PracticeSnapshot(Base):
    __tablename__ = "practice_snapshots"
    __table_args__ = (
        CheckConstraint("schema_version > 0", name="positive_schema_version"),
        CheckConstraint("generation > 0", name="positive_generation"),
        CheckConstraint("version > 0", name="positive_version"),
        CheckConstraint("jsonb_typeof(state) = 'object'", name="state_object"),
    )

    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    schema_version: Mapped[int] = mapped_column(Integer)
    generation: Mapped[int] = mapped_column(BigInteger)
    version: Mapped[int] = mapped_column(BigInteger)
    state: Mapped[dict[str, Any]] = mapped_column(JSONB)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped[PracticeSession] = relationship(back_populates="snapshot")
