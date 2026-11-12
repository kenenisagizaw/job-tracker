from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.user import User
from app.repositories.company_repository import CompanyRepository
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyAlreadyExistsError(Exception):
    pass


class CompanyNotFoundError(Exception):
    pass


class CompanyInUseError(Exception):
    pass


class CompanyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CompanyRepository(db)

    def list_companies(self, current_user: User) -> list[Company]:
        return self.repository.list_for_owner(current_user.id)

    def create_company(self, payload: CompanyCreate, current_user: User) -> Company:
        name = " ".join(payload.name.split())
        if self.repository.get_by_name(name, current_user.id):
            raise CompanyAlreadyExistsError("Company already exists")

        try:
            company = self.repository.add(
                Company(name=name, owner_id=current_user.id)
            )
            self.db.commit()
            self.db.refresh(company)
            return company
        except IntegrityError as error:
            self.db.rollback()
            raise CompanyAlreadyExistsError("Company already exists") from error
        except Exception:
            self.db.rollback()
            raise

    def update_company(
        self,
        company_id: int,
        payload: CompanyUpdate,
        current_user: User,
    ) -> Company:
        company = self.repository.get_for_owner(company_id, current_user.id)
        if company is None:
            raise CompanyNotFoundError("Company not found")

        name = " ".join(payload.name.split())
        existing = self.repository.get_by_name(name, current_user.id)
        if existing and existing.id != company.id:
            raise CompanyAlreadyExistsError("Company already exists")

        company.name = name
        try:
            self.db.commit()
            self.db.refresh(company)
            return company
        except IntegrityError as error:
            self.db.rollback()
            raise CompanyAlreadyExistsError("Company already exists") from error

    def delete_company(self, company_id: int, current_user: User) -> None:
        company = self.repository.get_for_owner(company_id, current_user.id)
        if company is None:
            raise CompanyNotFoundError("Company not found")
        if self.repository.job_count(company_id):
            raise CompanyInUseError("Company is referenced by a job")

        self.db.delete(company)
        self.db.commit()
