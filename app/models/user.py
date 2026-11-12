from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.interview import Interview
    from app.models.job import Job


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    jobs: Mapped[list["Job"]] = relationship(back_populates="owner")
    companies: Mapped[list["Company"]] = relationship(back_populates="owner")
    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )