from __future__ import annotations

from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    Date,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Job(Base):
    __tablename__ = "jobs"

    __table_args__ = (
        CheckConstraint("salary IS NULL OR salary > 0", name="check_salary_positive"),
        CheckConstraint(
            "status IN ('saved', 'applied', 'interview', 'offer', 'rejected')",
            name="check_job_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    owner: Mapped["User"] = relationship(back_populates="jobs")
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"), nullable=False, index=True
    )
    company: Mapped["Company"] = relationship(back_populates="jobs")
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    job_type: Mapped[str] = mapped_column(
        String(50), default="Full-time", nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="saved", nullable=False
    )
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    deadline_reminder_sent_for: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )