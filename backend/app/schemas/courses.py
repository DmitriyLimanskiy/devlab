from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Course(Timestamps, Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("position > 0", name="positive_position"),
        CheckConstraint(
            "status IN ('planned', 'available', 'archived')", name="valid_status"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, server_default=text("''"))
    status: Mapped[str] = mapped_column(String(20), server_default=text("'planned'"))
    position: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    steps: Mapped[list["CourseStep"]] = relationship(
        back_populates="course", order_by="CourseStep.position", passive_deletes="all"
    )


class CourseStep(Timestamps, Base):
    __tablename__ = "course_steps"
    __table_args__ = (
        UniqueConstraint(
            "course_id", "position", name="uq_course_steps_course_position"
        ),
        UniqueConstraint("course_id", "slug", name="uq_course_steps_course_slug"),
        CheckConstraint("position > 0", name="positive_position"),
        CheckConstraint("jsonb_typeof(content) = 'object'", name="content_object"),
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT")
    )
    slug: Mapped[str] = mapped_column(String(100))
    position: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb")
    )
    course: Mapped[Course] = relationship(back_populates="steps")
