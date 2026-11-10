from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.job import Job
from app.schemas.job import JobSortField, SortOrder


class JobRepository:
    """Database operations for jobs."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, job: Job) -> Job:
        self.db.add(job)
        return job

    def list(
        self,
        *,
        owner_id: int,
        search: str | None = None,
        location: str | None = None,
        company: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: JobSortField = JobSortField.id,
        sort_order: SortOrder = SortOrder.desc,
    ) -> list[Job]:
        statement = select(Job).where(Job.owner_id == owner_id)
        if search:
            search_pattern = f"%{search}%"
            statement = statement.join(Job.company).where(
                Job.title.ilike(search_pattern)
                | Job.description.ilike(search_pattern)
                | Job.location.ilike(search_pattern)
                | Company.name.ilike(search_pattern)
            )
        if location:
            statement = statement.where(Job.location.ilike(f"%{location}%"))
        if company:
            if not search:
                statement = statement.join(Job.company)
            statement = statement.where(Company.name.ilike(f"%{company}%"))
        if status:
            statement = statement.where(Job.status == status)
        sort_column = {
            JobSortField.id: Job.id,
            JobSortField.title: Job.title,
            JobSortField.location: Job.location,
            JobSortField.salary: Job.salary,
            JobSortField.status: Job.status,
        }[sort_by]
        order_expression = (
            sort_column.asc() if sort_order == SortOrder.asc else sort_column.desc()
        )
        statement = (
            statement.order_by(order_expression, Job.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(statement))

    def count(
        self,
        *,
        owner_id: int,
        search: str | None = None,
        location: str | None = None,
        company: str | None = None,
        status: str | None = None,
    ) -> int:
        statement = select(func.count()).select_from(Job).where(
            Job.owner_id == owner_id
        )
        if search:
            search_pattern = f"%{search}%"
            statement = statement.join(Job.company).where(
                Job.title.ilike(search_pattern)
                | Job.description.ilike(search_pattern)
                | Job.location.ilike(search_pattern)
                | Company.name.ilike(search_pattern)
            )
        if location:
            statement = statement.where(Job.location.ilike(f"%{location}%"))
        if company:
            if not search:
                statement = statement.join(Job.company)
            statement = statement.where(Company.name.ilike(f"%{company}%"))
        if status:
            statement = statement.where(Job.status == status)
        return self.db.scalar(statement) or 0

    def get(self, job_id: int, owner_id: int) -> Job | None:
        statement = select(Job).where(
            Job.id == job_id,
            Job.owner_id == owner_id,
        )
        return self.db.scalar(statement)

    def delete(self, job: Job) -> None:
        self.db.delete(job)
