from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company
from app.repositories.company_repository import CompanyRepository
from app.schemas.company import CompanyCreate


class CompanyAlreadyExistsError(Exception):
    pass


class CompanyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CompanyRepository(db)

    def list_companies(self) -> list[Company]:
        return self.repository.list()

    def create_company(self, payload: CompanyCreate) -> Company:
        name = " ".join(payload.name.split())
        if self.repository.get_by_name(name):
            raise CompanyAlreadyExistsError("Company already exists")

        try:
            company = self.repository.add(Company(name=name))
            self.db.commit()
            self.db.refresh(company)
            return company
        except IntegrityError as error:
            self.db.rollback()
            raise CompanyAlreadyExistsError("Company already exists") from error
        except Exception:
            self.db.rollback()
            raise
