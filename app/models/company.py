from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.user import User


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_companies_owner_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    owner: Mapped["User"] = relationship(back_populates="companies")
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    jobs: Mapped[list["Job"]] = relationship(back_populates="company")
