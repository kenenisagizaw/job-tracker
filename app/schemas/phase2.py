from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class DocumentRead(BaseModel):
    id: int
    job_id: int | None
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ContactFields(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr | None = None
    role: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=5000)
    company_id: int | None = Field(default=None, gt=0)
    job_id: int | None = Field(default=None, gt=0)


class ContactCreate(ContactFields):
    pass


class ContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    role: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=5000)
    company_id: int | None = Field(default=None, gt=0)
    job_id: int | None = Field(default=None, gt=0)


class ContactRead(ContactFields):
    id: int
    owner_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ReminderStatus(StrEnum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    due_at: datetime
    job_id: int | None = Field(default=None, gt=0)
    interview_id: int | None = Field(default=None, gt=0)

    @field_validator("due_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("due_at must include a timezone")
        return value


class ReminderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    due_at: datetime | None = None
    job_id: int | None = Field(default=None, gt=0)
    interview_id: int | None = Field(default=None, gt=0)
    status: ReminderStatus | None = None

    @field_validator("due_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("due_at must include a timezone")
        return value


class ReminderRead(BaseModel):
    id: int
    user_id: int
    title: str
    due_at: datetime
    job_id: int | None
    interview_id: int | None
    status: ReminderStatus
    attempt_count: int
    last_error: str | None
    processed_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class NotificationRead(BaseModel):
    id: int
    title: str
    message: str
    read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class NotificationDetail(NotificationRead):
    reminder_id: int | None


class UnreadNotificationCount(BaseModel):
    unread_count: int
