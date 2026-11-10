from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import DEADLINE_REMINDER_DAYS
from app.models.job import Job
from app.models.user import User
from app.services.notification_service import (
    job_deadline_reminder_email,
    send_job_notification,
)


def send_due_deadline_reminders(db: Session) -> int:
    today = date.today()
    latest = today + timedelta(days=DEADLINE_REMINDER_DAYS)
    jobs = db.scalars(
        select(Job)
        .join(Job.owner)
        .where(
            Job.deadline >= today,
            Job.deadline <= latest,
            Job.deadline_reminder_sent_for != Job.deadline,
            Job.status.notin_(("offer", "rejected")),
        )
    ).all()

    sent = 0
    for job in jobs:
        owner = db.get(User, job.owner_id)
        if owner is None:
            continue
        days_left = (job.deadline - today).days
        job.deadline_reminder_sent_for = job.deadline
        db.commit()
        subject, body, recipient = job_deadline_reminder_email(
            job.title,
            job.deadline.isoformat(),
            days_left,
            owner.email,
        )
        send_job_notification(recipient, subject, body)
        sent += 1
    return sent
