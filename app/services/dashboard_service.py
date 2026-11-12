from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.user import User
from app.schemas.dashboard import DashboardMetrics
from app.schemas.job import JobStatus


def get_dashboard_metrics(
    db: Session,
    current_user: User,
) -> DashboardMetrics:
    rows = db.execute(
        select(Job.status, func.count())
        .where(Job.owner_id == current_user.id)
        .group_by(Job.status)
    ).all()
    distribution = {status.value: 0 for status in JobStatus}
    distribution.update({status: count for status, count in rows})
    return DashboardMetrics(
        total_applications=sum(distribution.values()),
        status_distribution=distribution,
    )
