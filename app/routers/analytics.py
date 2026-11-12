from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.interview import Interview
from app.models.job import Job
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
def analytics_summary(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    statement = select(Job.status, func.count()).where(Job.owner_id == current_user.id)
    if start:
        statement = statement.where(Job.deadline >= start)
    if end:
        statement = statement.where(Job.deadline <= end)
    rows = db.execute(statement.group_by(Job.status)).all()
    distribution = {status: count for status, count in rows}
    total = sum(distribution.values())
    interviews = db.scalar(select(func.count()).select_from(Interview).where(Interview.user_id == current_user.id)) or 0
    offers = distribution.get("offer", 0)
    applied = distribution.get("applied", 0) + distribution.get("interview", 0) + offers + distribution.get("rejected", 0)
    return {
        "total_applications": total,
        "status_distribution": distribution,
        "interviews": interviews,
        "offers": offers,
        "application_to_interview_rate": round(interviews / applied * 100, 2) if applied else 0,
        "application_to_offer_rate": round(offers / total * 100, 2) if total else 0,
    }
