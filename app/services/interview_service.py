from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interview import Interview
from app.models.job import Job
from app.models.user import User
from app.schemas.interview import InterviewCreate, InterviewUpdate


class InterviewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_owned(self, interview_id: int, user_id: int) -> Interview:
        interview = self.db.scalar(
            select(Interview).where(
                Interview.id == interview_id,
                Interview.user_id == user_id,
            )
        )
        if interview is None:
            raise HTTPException(status_code=404, detail="Interview not found")
        return interview

    def _validate_job(self, job_id: int, user_id: int) -> None:
        if self.db.scalar(
            select(Job.id).where(Job.id == job_id, Job.owner_id == user_id)
        ) is None:
            raise HTTPException(status_code=404, detail="Job not found")

    def create(self, payload: InterviewCreate, user: User) -> Interview:
        self._validate_job(payload.job_id, user.id)
        interview = Interview(
            **payload.model_dump(),
            user_id=user.id,
        )
        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def list(
        self,
        user: User,
        *,
        job_id: int | None = None,
        stage: str | None = None,
        outcome: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Interview]:
        statement = select(Interview).where(Interview.user_id == user.id)
        if job_id is not None:
            statement = statement.where(Interview.job_id == job_id)
        if stage is not None:
            statement = statement.where(Interview.interview_stage == stage)
        if outcome is not None:
            statement = statement.where(Interview.outcome == outcome)
        if start is not None:
            statement = statement.where(Interview.scheduled_at >= start)
        if end is not None:
            statement = statement.where(Interview.scheduled_at <= end)
        statement = statement.order_by(Interview.scheduled_at).offset(skip).limit(limit)
        return list(self.db.scalars(statement))

    def upcoming(self, user: User, limit: int = 20) -> list[Interview]:
        return self.list(
            user,
            start=datetime.now(timezone.utc),
            limit=limit,
        )

    def get(self, interview_id: int, user: User) -> Interview:
        return self._get_owned(interview_id, user.id)

    def update(
        self,
        interview_id: int,
        payload: InterviewUpdate,
        user: User,
    ) -> Interview:
        interview = self._get_owned(interview_id, user.id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(interview, field, value)
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def delete(self, interview_id: int, user: User) -> None:
        interview = self._get_owned(interview_id, user.id)
        self.db.delete(interview)
        self.db.commit()
