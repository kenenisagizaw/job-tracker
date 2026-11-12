from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.user import User


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    interview_type: Mapped[str] = mapped_column(String(40), nullable=False)
    interview_stage: Mapped[str] = mapped_column(String(40), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meeting_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    interviewer_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    interviewer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preparation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="interviews")
    job: Mapped["Job"] = relationship(back_populates="interviews")
