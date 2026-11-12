from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.job import Job


class CompanyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[Company]:
        return list(self.db.scalars(select(Company).order_by(Company.name)))

    def list_for_owner(self, owner_id: int) -> list[Company]:
        statement = (
            select(Company)
            .where(Company.owner_id == owner_id)
            .order_by(Company.name)
        )
        return list(self.db.scalars(statement))

    def get_by_name(self, name: str, owner_id: int) -> Company | None:
        return self.db.scalar(
            select(Company).where(
                Company.name == name,
                Company.owner_id == owner_id,
            )
        )

    def get_for_owner(self, company_id: int, owner_id: int) -> Company | None:
        return self.db.scalar(
            select(Company).where(
                Company.id == company_id,
                Company.owner_id == owner_id,
            )
        )

    def job_count(self, company_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(Job)
                .where(Job.company_id == company_id)
            )
            or 0
        )

    def add(self, company: Company) -> Company:
        self.db.add(company)
        return company
