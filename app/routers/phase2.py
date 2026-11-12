from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import (
    ALLOWED_DOCUMENT_EXTENSIONS,
    DOCUMENT_STORAGE_PATH,
    MAX_DOCUMENT_SIZE_BYTES,
)
from app.db.database import get_db
from app.models.company import Company
from app.models.interview import Interview
from app.models.phase2 import Contact, Document, Notification, Reminder
from app.models.job import Job
from app.models.user import User
from app.schemas.phase2 import (
    ContactCreate,
    ContactRead,
    ContactUpdate,
    DocumentRead,
    NotificationRead,
    NotificationDetail,
    ReminderCreate,
    ReminderRead,
    ReminderUpdate,
    UnreadNotificationCount,
)

router = APIRouter(tags=["phase2"])


def owned_job(db: Session, job_id: int | None, user_id: int) -> None:
    if job_id is not None and db.scalar(select(Job.id).where(Job.id == job_id, Job.owner_id == user_id)) is None:
        raise HTTPException(404, "Job not found")


def owned_company(db: Session, company_id: int | None, user_id: int) -> None:
    if company_id is not None and db.scalar(
        select(Company.id).where(
            Company.id == company_id,
            Company.owner_id == user_id,
        )
    ) is None:
        raise HTTPException(404, "Company not found")


def validate_contact_references(
    db: Session,
    *,
    company_id: int | None,
    job_id: int | None,
    user_id: int,
) -> None:
    owned_company(db, company_id, user_id)
    owned_job(db, job_id, user_id)


def owned_interview(db: Session, interview_id: int | None, user_id: int) -> None:
    if interview_id is not None and db.scalar(
        select(Interview.id).where(
            Interview.id == interview_id,
            Interview.user_id == user_id,
        )
    ) is None:
        raise HTTPException(404, "Interview not found")


def validate_reminder_references(
    db: Session,
    *,
    job_id: int | None,
    interview_id: int | None,
    user_id: int,
) -> None:
    owned_job(db, job_id, user_id)
    owned_interview(db, interview_id, user_id)


def user_storage_directory(user_id: int) -> Path:
    directory = (DOCUMENT_STORAGE_PATH / str(user_id)).resolve()
    storage_root = DOCUMENT_STORAGE_PATH.resolve()
    if storage_root not in directory.parents:
        raise RuntimeError("Document storage path escaped its configured root")
    directory.mkdir(parents=True, exist_ok=True, mode=0o750)
    return directory


@router.post("/documents", response_model=DocumentRead, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    job_id: int | None = Query(default=None, gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Document:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(400, "Unsupported document type")
    data = await file.read()
    if len(data) > MAX_DOCUMENT_SIZE_BYTES:
        raise HTTPException(413, "Document exceeds the configured size limit")
    owned_job(db, job_id, current_user.id)
    stored_name = f"{uuid4().hex}{extension}"
    target = user_storage_directory(current_user.id)
    (target / stored_name).write_bytes(data)
    document = Document(user_id=current_user.id, job_id=job_id, filename=Path(file.filename or "document").name, stored_name=stored_name, content_type=file.content_type or "application/octet-stream", size_bytes=len(data))
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/documents", response_model=list[DocumentRead])
def list_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Document]:
    return list(db.scalars(select(Document).where(Document.user_id == current_user.id).order_by(Document.created_at.desc())))


@router.get("/documents/{document_id}/download")
def download_document(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> FileResponse:
    document = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == current_user.id))
    if document is None:
        raise HTTPException(404, "Document not found")
    path = user_storage_directory(current_user.id) / document.stored_name
    if not path.is_file():
        raise HTTPException(404, "Document file is unavailable")
    return FileResponse(path, media_type=document.content_type, filename=document.filename)


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    document = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == current_user.id))
    if document is None:
        raise HTTPException(404, "Document not found")
    path = user_storage_directory(current_user.id) / document.stored_name
    if path.exists():
        path.unlink()
    db.delete(document)
    db.commit()


@router.post("/contacts", response_model=ContactRead, status_code=201)
def create_contact(payload: ContactCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Contact:
    validate_contact_references(
        db,
        company_id=payload.company_id,
        job_id=payload.job_id,
        user_id=current_user.id,
    )
    contact = Contact(**payload.model_dump(), owner_id=current_user.id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/contacts", response_model=list[ContactRead])
def list_contacts(
    search: str | None = Query(default=None, min_length=1, max_length=100),
    company_id: int | None = Query(default=None, gt=0),
    job_id: int | None = Query(default=None, gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Contact]:
    statement = select(Contact).where(Contact.owner_id == current_user.id)
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            Contact.name.ilike(pattern)
            | Contact.email.ilike(pattern)
            | Contact.role.ilike(pattern)
        )
    if company_id is not None:
        statement = statement.where(Contact.company_id == company_id)
    if job_id is not None:
        statement = statement.where(Contact.job_id == job_id)
    return list(db.scalars(statement.order_by(Contact.name)))


@router.get("/contacts/{contact_id}", response_model=ContactRead)
def get_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Contact:
    contact = db.scalar(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.owner_id == current_user.id,
        )
    )
    if contact is None:
        raise HTTPException(404, "Contact not found")
    return contact


@router.patch("/contacts/{contact_id}", response_model=ContactRead)
def update_contact(contact_id: int, payload: ContactUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Contact:
    contact = db.scalar(select(Contact).where(Contact.id == contact_id, Contact.owner_id == current_user.id))
    if contact is None:
        raise HTTPException(404, "Contact not found")
    values = payload.model_dump(exclude_unset=True)
    validate_contact_references(
        db,
        company_id=values.get("company_id", contact.company_id),
        job_id=values.get("job_id", contact.job_id),
        user_id=current_user.id,
    )
    for key, value in values.items():
        setattr(contact, key, value)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    contact = db.scalar(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.owner_id == current_user.id,
        )
    )
    if contact is None:
        raise HTTPException(404, "Contact not found")
    db.delete(contact)
    db.commit()


@router.post("/reminders", response_model=ReminderRead, status_code=201)
def create_reminder(payload: ReminderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Reminder:
    validate_reminder_references(
        db,
        job_id=payload.job_id,
        interview_id=payload.interview_id,
        user_id=current_user.id,
    )
    reminder = Reminder(**payload.model_dump(), user_id=current_user.id)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("/reminders", response_model=list[ReminderRead])
def list_reminders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Reminder]:
    return list(db.scalars(select(Reminder).where(Reminder.user_id == current_user.id).order_by(Reminder.due_at)))


@router.get("/reminders/{reminder_id}", response_model=ReminderRead)
def get_reminder(reminder_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Reminder:
    reminder = db.scalar(select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id))
    if reminder is None:
        raise HTTPException(404, "Reminder not found")
    return reminder


@router.patch("/reminders/{reminder_id}", response_model=ReminderRead)
def update_reminder(
    reminder_id: int,
    payload: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Reminder:
    reminder = db.scalar(select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id))
    if reminder is None:
        raise HTTPException(404, "Reminder not found")
    values = payload.model_dump(exclude_unset=True)
    validate_reminder_references(
        db,
        job_id=values.get("job_id", reminder.job_id),
        interview_id=values.get("interview_id", reminder.interview_id),
        user_id=current_user.id,
    )
    if "due_at" in values and values["due_at"] != reminder.due_at:
        reminder.processed_at = None
        reminder.processing_started_at = None
        reminder.last_error = None
        reminder.attempt_count = 0
        if reminder.status != "completed":
            reminder.status = "pending"
    for key, value in values.items():
        setattr(reminder, key, value.value if hasattr(value, "value") else value)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.post("/reminders/{reminder_id}/snooze", response_model=ReminderRead)
def snooze_reminder(
    reminder_id: int,
    minutes: int = Query(default=60, gt=0, le=10080),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Reminder:
    reminder = db.scalar(select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id))
    if reminder is None:
        raise HTTPException(404, "Reminder not found")
    if reminder.status == "completed":
        raise HTTPException(409, "Completed reminders cannot be snoozed")
    reminder.due_at = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    reminder.status = "pending"
    reminder.processing_started_at = None
    reminder.processed_at = None
    reminder.last_error = None
    db.commit()
    db.refresh(reminder)
    return reminder


@router.patch("/reminders/{reminder_id}/complete", response_model=ReminderRead)
def complete_reminder(reminder_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Reminder:
    reminder = db.scalar(select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id))
    if reminder is None:
        raise HTTPException(404, "Reminder not found")
    reminder.status = "completed"
    reminder.processing_started_at = None
    reminder.processed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.delete("/reminders/{reminder_id}", status_code=204)
def delete_reminder(reminder_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    reminder = db.scalar(select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id))
    if reminder is None:
        raise HTTPException(404, "Reminder not found")
    db.delete(reminder)
    db.commit()


@router.get("/notifications", response_model=list[NotificationDetail])
def list_notifications(
    unread_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Notification]:
    statement = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        statement = statement.where(Notification.read.is_(False))
    return list(db.scalars(statement.order_by(Notification.created_at.desc()).offset(skip).limit(limit)))


@router.get("/notifications/unread-count", response_model=UnreadNotificationCount)
def unread_notification_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UnreadNotificationCount:
    count = db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == current_user.id,
            Notification.read.is_(False),
        )
    ) or 0
    return UnreadNotificationCount(unread_count=count)


@router.patch("/notifications/read-all", response_model=UnreadNotificationCount)
def mark_all_notifications_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UnreadNotificationCount:
    notifications = db.scalars(select(Notification).where(Notification.user_id == current_user.id, Notification.read.is_(False))).all()
    for notification in notifications:
        notification.read = True
    db.commit()
    return UnreadNotificationCount(unread_count=0)


@router.get("/notifications/{notification_id}", response_model=NotificationDetail)
def get_notification(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Notification:
    notification = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id))
    if notification is None:
        raise HTTPException(404, "Notification not found")
    return notification


@router.patch("/notifications/{notification_id}/read", response_model=NotificationRead)
def read_notification(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Notification:
    notification = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id))
    if notification is None:
        raise HTTPException(404, "Notification not found")
    notification.read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.delete("/notifications/{notification_id}", status_code=204)
def delete_notification(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    notification = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id))
    if notification is None:
        raise HTTPException(404, "Notification not found")
    db.delete(notification)
    db.commit()
