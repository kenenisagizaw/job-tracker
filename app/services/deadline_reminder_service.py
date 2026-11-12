from datetime import date, datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import DEADLINE_REMINDER_DAYS
from app.models.job import Job
from app.models.user import User
from app.models.phase2 import Notification, Reminder
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


def create_due_reminder_notifications(db: Session) -> int:
    now = datetime.now(timezone.utc)
    stale_before = now - timedelta(minutes=10)
    reminders = db.scalars(
        select(Reminder)
        .where(
            Reminder.due_at <= now,
            Reminder.status == "pending",
            or_(
                Reminder.processing_started_at.is_(None),
                Reminder.processing_started_at < stale_before,
            ),
        )
        .with_for_update(skip_locked=True)
        .limit(50)
    ).all()
    created = 0
    for reminder in reminders:
        reminder.processing_started_at = now
        reminder.attempt_count += 1
        try:
            existing = db.scalar(
                select(Notification.id).where(Notification.reminder_id == reminder.id)
            )
            if existing is None:
                db.add(Notification(
                    user_id=reminder.user_id,
                    reminder_id=reminder.id,
                    title="Reminder due",
                    message=reminder.title,
                ))
            reminder.status = "completed"
            reminder.processed_at = now
            reminder.processing_started_at = None
            reminder.last_error = None
            created += 1
            db.commit()
        except Exception as error:
            db.rollback()
            reminder = db.get(Reminder, reminder.id)
            if reminder is not None:
                reminder.processing_started_at = None
                reminder.last_error = str(error)[:2000]
                if reminder.attempt_count >= 5:
                    reminder.status = "cancelled"
                db.commit()
    return created
