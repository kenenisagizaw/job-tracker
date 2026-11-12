from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class InterviewType(StrEnum):
    phone = "phone"
    video = "video"
    in_person = "in_person"
    technical_assessment = "technical_assessment"
    other = "other"


class InterviewStage(StrEnum):
    screening = "screening"
    technical = "technical"
    behavioral = "behavioral"
    final = "final"
    other = "other"


class InterviewOutcome(StrEnum):
    pending = "pending"
    passed = "passed"
    failed = "failed"
    rescheduled = "rescheduled"
    cancelled = "cancelled"


class InterviewFields(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    interview_type: InterviewType
    interview_stage: InterviewStage
    scheduled_at: datetime
    duration_minutes: int = Field(gt=0, le=1440)
    location: str | None = Field(default=None, max_length=255)
    meeting_link: str | None = Field(default=None, max_length=500)
    interviewer_name: str | None = Field(default=None, max_length=150)
    interviewer_email: EmailStr | None = None
    preparation_notes: str | None = Field(default=None, max_length=10000)
    feedback: str | None = Field(default=None, max_length=10000)
    outcome: InterviewOutcome = InterviewOutcome.pending

    @field_validator("scheduled_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("scheduled_at must include a timezone")
        return value


class InterviewCreate(InterviewFields):
    job_id: int = Field(gt=0)


class InterviewUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    interview_type: InterviewType | None = None
    interview_stage: InterviewStage | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0, le=1440)
    location: str | None = Field(default=None, max_length=255)
    meeting_link: str | None = Field(default=None, max_length=500)
    interviewer_name: str | None = Field(default=None, max_length=150)
    interviewer_email: EmailStr | None = None
    preparation_notes: str | None = Field(default=None, max_length=10000)
    feedback: str | None = Field(default=None, max_length=10000)
    outcome: InterviewOutcome | None = None

    @field_validator("scheduled_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("scheduled_at must include a timezone")
        return value


class InterviewRead(InterviewFields):
    id: int
    user_id: int
    job_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("scheduled_at", mode="before")
    @classmethod
    def normalize_database_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
