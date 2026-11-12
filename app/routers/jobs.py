from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.job import Job
from app.models.user import User
from app.schemas.job import (
    JobCreate,
    JobRead,
    JobSortField,
    JobStatus,
    JobStatusUpdate,
    JobUpdate,
    SortOrder,
)
from app.schemas.activity import ActivityRead
from app.models.activity import ApplicationActivity
from app.services.job_service import JobService
from app.services.notification_service import (
    job_created_email,
    job_status_changed_email,
    send_job_notification,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    job = JobService(db).create_job(payload, current_user)
    subject, body, recipient = job_created_email(job.title, current_user.email)
    background_tasks.add_task(send_job_notification, recipient, subject, body)
    return job


@router.get("", response_model=list[JobRead])
def list_jobs(
    search: str | None = Query(default=None, min_length=1, max_length=100),
    location: str | None = Query(default=None),
    company: str | None = Query(default=None),
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    sort_by: JobSortField = Query(default=JobSortField.id),
    sort_order: SortOrder = Query(default=SortOrder.desc),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Job]:
    return JobService(db).list_jobs(
        current_user=current_user,
        search=search,
        location=location,
        company=company,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/count")
def count_jobs(
    search: str | None = Query(default=None, min_length=1, max_length=100),
    location: str | None = Query(default=None),
    company: str | None = Query(default=None),
    status_filter: JobStatus | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    return {
        "count": JobService(db).count_jobs(
            current_user,
            search=search,
            location=location,
            company=company,
            status_filter=status_filter,
        )
    }


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    return JobService(db).get_job(job_id, current_user)


@router.get("/{job_id}/activities", response_model=list[ActivityRead])
def list_job_activities(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ApplicationActivity]:
    job = JobService(db).get_job(job_id, current_user)
    return list(
        db.scalars(
            select(ApplicationActivity)
            .where(ApplicationActivity.job_id == job.id)
            .order_by(ApplicationActivity.created_at, ApplicationActivity.id)
        )
    )


@router.put("/{job_id}", response_model=JobRead)
def replace_job(
    job_id: int,
    payload: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    return JobService(db).replace_job(job_id, payload, current_user)


@router.patch("/{job_id}/status", response_model=JobRead)
def update_job_status(
    job_id: int,
    payload: JobStatusUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    service = JobService(db)
    old_status = service.get_job(job_id, current_user).status
    job = service.update_job_status(job_id, payload, current_user)
    if old_status != job.status:
        subject, body, recipient = job_status_changed_email(
            job.title,
            old_status,
            job.status,
            current_user.email,
        )
        background_tasks.add_task(send_job_notification, recipient, subject, body)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    JobService(db).delete_job(job_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
