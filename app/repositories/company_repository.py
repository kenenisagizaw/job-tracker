from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company


class CompanyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[Company]:
        return list(self.db.scalars(select(Company).order_by(Company.name)))

    def get_by_name(self, name: str) -> Company | None:
        return self.db.scalar(select(Company).where(Company.name == name))

    def add(self, company: Company) -> Company:
        self.db.add(company)
        return company
