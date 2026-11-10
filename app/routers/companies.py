from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyRead
from app.services.company_service import (
    CompanyAlreadyExistsError,
    CompanyService,
)

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyRead])
def list_companies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Company]:
    return CompanyService(db).list_companies()


@router.post(
    "",
    response_model=CompanyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_company(
    payload: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Company:
    try:
        return CompanyService(db).create_company(payload)
    except CompanyAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
