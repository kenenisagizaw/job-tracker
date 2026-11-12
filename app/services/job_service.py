from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.user import User
from app.models.activity import ApplicationActivity
from app.repositories.job_repository import JobRepository
from app.repositories.company_repository import CompanyRepository
from app.schemas.job import (
    JobCreate,
    JobSortField,
    JobStatus,
    JobStatusUpdate,
    JobUpdate,
    SortOrder,
)


class JobService:
    """Coordinates job use cases and their database transactions."""

    def __init__(self, db: Session) -> None:
        self.repository = JobRepository(db)
        self.company_repository = CompanyRepository(db)
        self.db = db

    def create_job(self, payload: JobCreate, current_user: User) -> Job:
        if not self.company_repository.get_for_owner(
            payload.company_id,
            current_user.id,
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )
        job = self.repository.add(
            Job(**payload.model_dump(), owner_id=current_user.id)
        )
        self.db.commit()
        self.db.refresh(job)
        self.db.add(
            ApplicationActivity(
                job_id=job.id,
                event_type="job_created",
                description=f"Job '{job.title}' was added to the pipeline.",
            )
        )
        self.db.commit()
        self.db.refresh(job)
        return job

    def list_jobs(
        self,
        *,
        current_user: User,
        search: str | None = None,
        location: str | None = None,
        company: str | None = None,
        status_filter: JobStatus | None = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: JobSortField = JobSortField.id,
        sort_order: SortOrder = SortOrder.desc,
    ) -> list[Job]:
        return self.repository.list(
            owner_id=current_user.id,
            search=search,
            location=location,
            company=company,
            status=status_filter.value if status_filter else None,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def count_jobs(
        self,
        current_user: User,
        *,
        search: str | None = None,
        location: str | None = None,
        company: str | None = None,
        status_filter: JobStatus | None = None,
    ) -> int:
        return self.repository.count(
            owner_id=current_user.id,
            search=search,
            location=location,
            company=company,
            status=status_filter.value if status_filter else None,
        )

    def get_job(self, job_id: int, current_user: User) -> Job:
        job = self.repository.get(job_id, current_user.id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )
        return job

    def replace_job(
        self, job_id: int, payload: JobUpdate, current_user: User
    ) -> Job:
        job = self.get_job(job_id, current_user)
        if not self.company_repository.get_for_owner(
            payload.company_id,
            current_user.id,
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )
        for field, value in payload.model_dump().items():
            setattr(job, field, value)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job_status(
        self,
        job_id: int,
        payload: JobStatusUpdate,
        current_user: User,
    ) -> Job:
        job = self.get_job(job_id, current_user)
        old_status = job.status
        job.status = payload.status.value
        self.db.add(
            ApplicationActivity(
                job_id=job.id,
                event_type="status_changed",
                description=(
                    f"Status changed from '{old_status}' "
                    f"to '{payload.status.value}'."
                ),
            )
        )
        self.db.commit()
        self.db.refresh(job)
        return job

    def delete_job(self, job_id: int, current_user: User) -> None:
        job = self.get_job(job_id, current_user)
        self.repository.delete(job)
        self.db.commit()
