from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.interview import Interview
from app.models.user import User
from app.schemas.interview import InterviewCreate, InterviewRead, InterviewUpdate
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interviews", tags=["interviews"])
job_interviews_router = APIRouter(tags=["interviews"])


@router.post("", response_model=InterviewRead, status_code=status.HTTP_201_CREATED)
def create_interview(
    payload: InterviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Interview:
    return InterviewService(db).create(payload, current_user)


@router.get("", response_model=list[InterviewRead])
def list_interviews(
    job_id: int | None = Query(default=None, gt=0),
    stage: str | None = None,
    outcome: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Interview]:
    return InterviewService(db).list(
        current_user,
        job_id=job_id,
        stage=stage,
        outcome=outcome,
        start=start,
        end=end,
        skip=skip,
        limit=limit,
    )


@router.get("/upcoming", response_model=list[InterviewRead])
def upcoming_interviews(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Interview]:
    return InterviewService(db).upcoming(current_user, limit)


@job_interviews_router.get(
    "/jobs/{job_id}/interviews",
    response_model=list[InterviewRead],
)
def list_job_interviews(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Interview]:
    return InterviewService(db).list(current_user, job_id=job_id)


@router.get("/{interview_id}", response_model=InterviewRead)
def get_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Interview:
    return InterviewService(db).get(interview_id, current_user)


@router.patch("/{interview_id}", response_model=InterviewRead)
def update_interview(
    interview_id: int,
    payload: InterviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Interview:
    return InterviewService(db).update(interview_id, payload, current_user)


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    InterviewService(db).delete(interview_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
