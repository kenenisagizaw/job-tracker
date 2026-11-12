from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityRead(BaseModel):
    id: int
    job_id: int
    event_type: str
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
