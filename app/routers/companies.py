from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyRead, CompanyUpdate
from app.services.company_service import (
    CompanyAlreadyExistsError,
    CompanyInUseError,
    CompanyNotFoundError,
    CompanyService,
)

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyRead])
def list_companies(
    search: str | None = Query(default=None, min_length=1, max_length=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Company]:
    companies = CompanyService(db).list_companies(current_user)
    if search:
        search_lower = search.lower()
        companies = [
            company for company in companies if search_lower in company.name.lower()
        ]
    return companies


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
        return CompanyService(db).create_company(payload, current_user)
    except CompanyAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.put("/{company_id}", response_model=CompanyRead)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Company:
    try:
        return CompanyService(db).update_company(company_id, payload, current_user)
    except CompanyNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except CompanyAlreadyExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        CompanyService(db).delete_company(company_id, current_user)
    except CompanyNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except CompanyInUseError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
