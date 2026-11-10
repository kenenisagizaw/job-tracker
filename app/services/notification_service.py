import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import (
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
)

logger = logging.getLogger(__name__)


def send_job_notification(recipient: str, subject: str, body: str) -> None:
    if not all((SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM)):
        logger.error("Job email notification skipped: SMTP is not configured")
        return

    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP_SSL(
            SMTP_HOST,
            SMTP_PORT,
            context=ssl.create_default_context(),
            timeout=10,
        ) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        logger.exception("Job email notification delivery failed")


def job_created_email(job_title: str, recipient: str) -> tuple[str, str, str]:
    return (
        "Job created",
        f"Your job tracking entry for '{job_title}' was created.",
        recipient,
    )


def job_status_changed_email(
    job_title: str,
    old_status: str,
    new_status: str,
    recipient: str,
) -> tuple[str, str, str]:
    return (
        "Job status updated",
        (
            f"The status for '{job_title}' changed from "
            f"'{old_status}' to '{new_status}'."
        ),
        recipient,
    )


def job_deadline_reminder_email(
    job_title: str,
    deadline: str,
    days_left: int,
    recipient: str,
) -> tuple[str, str, str]:
    return (
        f"Deadline reminder: {job_title}",
        (
            f"Your job tracking entry for '{job_title}' has a deadline on "
            f"{deadline}. There are {days_left} day(s) left."
        ),
        recipient,
    )
