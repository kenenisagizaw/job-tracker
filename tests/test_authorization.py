import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://user:pass@localhost/db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-bytes")

from fastapi import HTTPException
from fastapi.routing import APIRoute
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import Base
from app.models.company import Company
from app.models.user import User
from app.api.v1.endpoints.auth import _check_login_rate_limit
from app.core.config import LOGIN_RATE_LIMIT
from app.routers.jobs import router
from app.schemas.job import JobCreate, JobSortField, SortOrder
from app.schemas.user import UserCreate
from app.services import auth_service
from app.services.job_service import JobService
from app.services.notification_service import (
    job_created_email,
    job_status_changed_email,
)


def test_all_job_routes_require_authentication() -> None:
    routes = [route for route in router.routes if isinstance(route, APIRoute)]

    assert routes
    for route in routes:
        dependency_callables = {
            dependency.call for dependency in route.dependant.dependencies
        }
        assert get_current_user in dependency_callables


def test_jobs_are_scoped_and_queryable_per_authenticated_user() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        company = Company(name="Acme")
        first_user = User(email="first@example.com", hashed_password="hash")
        second_user = User(email="second@example.com", hashed_password="hash")
        db.add_all([company, first_user, second_user])
        db.commit()
        db.refresh(first_user)
        db.refresh(second_user)

        service = JobService(db)
        service.create_job(
            JobCreate(
                title="Backend Engineer",
                company_id=company.id,
                location="Remote",
                description="Python API",
            ),
            first_user,
        )
        service.create_job(
            JobCreate(
                title="Frontend Engineer",
                company_id=company.id,
                location="Office",
            ),
            first_user,
        )
        other_job = service.create_job(
            JobCreate(
                title="Security Engineer",
                company_id=company.id,
                location="Remote",
            ),
            second_user,
        )

        assert len(
            service.list_jobs(
                current_user=first_user,
                search="Python",
                sort_by=JobSortField.title,
                sort_order=SortOrder.asc,
                limit=1,
            )
        ) == 1
        assert service.list_jobs(current_user=first_user, limit=100)
        assert service.list_jobs(current_user=second_user) == [other_job]
        assert service.count_jobs(first_user, location="Remote") == 1

        assert service.count_jobs(first_user) == 2


def test_cross_user_job_access_raises_not_found() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        company = Company(name="Acme")
        owner = User(email="owner@example.com", hashed_password="hash")
        other_user = User(email="other@example.com", hashed_password="hash")
        db.add_all([company, owner, other_user])
        db.commit()
        db.refresh(owner)
        db.refresh(other_user)
        job = JobService(db).create_job(
            JobCreate(title="Engineer", company_id=company.id, location="Remote"),
            owner,
        )

        try:
            JobService(db).get_job(job.id, other_user)
        except HTTPException as error:
            assert error.status_code == 404
        else:
            raise AssertionError("A user accessed another user's job")


def test_registration_and_login_issue_a_token() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        user = auth_service.register_user(
            db,
            UserCreate(email="login@example.com", password="correct horse"),
        )
        token = auth_service.authenticate_user(
            db,
            email=user.email,
            password="correct horse",
        )

        assert token


def test_login_rate_limit_rejects_excess_attempts() -> None:
    class FakeRedis:
        def __init__(self) -> None:
            self.values: dict[str, int] = {}
            self.expirations: dict[str, int] = {}

        def incr(self, key: str) -> int:
            self.values[key] = self.values.get(key, 0) + 1
            return self.values[key]

        def expire(self, key: str, seconds: int) -> bool:
            self.expirations[key] = seconds
            return True

    client = FakeRedis()
    client_key = "rate-limit-test"
    for _ in range(LOGIN_RATE_LIMIT):
        _check_login_rate_limit(client_key, client)

    try:
        _check_login_rate_limit(client_key, client)
    except HTTPException as error:
        assert error.status_code == 429
    else:
        raise AssertionError("Login rate limit did not reject excess attempts")

    assert client.expirations[f"auth:login:rate:{client_key}"] == 60


def test_job_notification_content() -> None:
    subject, body, recipient = job_created_email(
        "Backend Engineer", "user@example.com"
    )
    assert subject == "Job created"
    assert "Backend Engineer" in body
    assert recipient == "user@example.com"

    subject, body, recipient = job_status_changed_email(
        "Backend Engineer",
        "saved",
        "applied",
        "user@example.com",
    )
    assert subject == "Job status updated"
    assert "saved" in body and "applied" in body
    assert recipient == "user@example.com"
