from enum import StrEnum
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(StrEnum):
    saved = "saved"
    applied = "applied"
    interview = "interview"
    offer = "offer"
    rejected = "rejected"


class JobSortField(StrEnum):
    id = "id"
    title = "title"
    location = "location"
    salary = "salary"
    status = "status"


class SortOrder(StrEnum):
    asc = "asc"
    desc = "desc"


class JobCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    company_id: int = Field(gt=0)
    location: str = Field(min_length=1, max_length=100)
    salary: Optional[float] = Field(default=None, gt=0)
    job_type: str = Field(default="Full-time", max_length=50)
    description: Optional[str] = Field(default=None, max_length=5000)
    deadline: date | None = None


class JobUpdate(JobCreate):
    pass


class JobRead(JobCreate):
    id: int
    status: JobStatus
    deadline_reminder_sent_for: date | None = None

    model_config = ConfigDict(from_attributes=True)


class JobStatusUpdate(BaseModel):
    status: JobStatus