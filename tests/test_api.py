import asyncio
import os
import sys
from collections.abc import Iterator

import httpx
import pytest
import stat
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://localhost/db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-bytes")

from app.api.deps import get_db
from app.api.v1.endpoints import auth, health
from app.db.database import Base
from app.main import app
from app.routers import jobs as jobs_module
from app.routers import phase2 as phase2_module
from app.services.deadline_reminder_service import create_due_reminder_notifications


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(db_session: Session) -> Iterator[httpx.Client]:
    def override_get_db() -> Iterator[Session]:
        yield db_session

    original_rate_limit = auth._check_login_rate_limit
    original_notification_sender = jobs_module.send_job_notification
    app.dependency_overrides[get_db] = override_get_db

    def bypass_rate_limit(
        _client_key: str,
        _client: object = auth.redis_client,
    ) -> None:
        del _client_key, _client
        return None

    auth._check_login_rate_limit = bypass_rate_limit
    jobs_module.send_job_notification = lambda *_args: None

    async def request(
        method: str,
        path: str,
        **kwargs: object,
    ) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as async_client:
            return await async_client.request(method, path, **kwargs)

    class SyncClient:
        def request(
            self,
            method: str,
            path: str,
            **kwargs: object,
        ) -> httpx.Response:
            return asyncio.run(request(method, path, **kwargs))

        def post(self, path: str, **kwargs: object) -> httpx.Response:
            return self.request("POST", path, **kwargs)

        def get(self, path: str, **kwargs: object) -> httpx.Response:
            return self.request("GET", path, **kwargs)

        def patch(self, path: str, **kwargs: object) -> httpx.Response:
            return self.request("PATCH", path, **kwargs)

        def put(self, path: str, **kwargs: object) -> httpx.Response:
            return self.request("PUT", path, **kwargs)

        def delete(self, path: str, **kwargs: object) -> httpx.Response:
            return self.request("DELETE", path, **kwargs)

    try:
        yield SyncClient()
    finally:
        app.dependency_overrides.clear()
        auth._check_login_rate_limit = original_rate_limit
        jobs_module.send_job_notification = original_notification_sender


def register_and_login(
    client: httpx.Client,
    email: str,
) -> str:
    registration = client.post(
        "/auth/register",
        json={"email": email, "password": "password-123"},
    )
    assert registration.status_code == 201

    login = client.post(
        "/auth/token",
        data={"username": email, "password": "password-123"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def test_authentication_endpoints_issue_and_accept_token(
    client: httpx.Client,
) -> None:
    token = register_and_login(client, "api-user@example.com")

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "api-user@example.com"


def test_job_routes_enforce_authenticated_ownership(
    client: httpx.Client,
) -> None:
    owner_token = register_and_login(client, "owner-api@example.com")
    other_token = register_and_login(client, "other-api@example.com")

    company = client.post(
        "/companies",
        json={"name": "API Company"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert company.status_code == 201

    other_company = client.post(
        "/companies",
        json={"name": "API Company"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_company.status_code == 201

    owner_companies = client.get(
        "/companies",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert [item["id"] for item in owner_companies.json()] == [
        company.json()["id"]
    ]

    renamed_company = client.put(
        f"/companies/{company.json()['id']}",
        json={"name": "API Company Updated"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert renamed_company.status_code == 200

    searched_companies = client.get(
        "/companies?search=updated",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert [item["name"] for item in searched_companies.json()] == [
        "API Company Updated"
    ]

    job = client.post(
        "/jobs",
        json={
            "title": "Backend Engineer",
            "company_id": company.json()["id"],
            "location": "Remote",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert job.status_code == 201
    job_id = job.json()["id"]

    metrics = client.get(
        "/dashboard/metrics",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert metrics.status_code == 200
    assert metrics.json() == {
        "total_applications": 1,
        "status_distribution": {
            "saved": 1,
            "applied": 0,
            "interview": 0,
            "offer": 0,
            "rejected": 0,
        },
    }

    activities = client.get(
        f"/jobs/{job_id}/activities",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert activities.status_code == 200
    assert activities.json()[0]["event_type"] == "job_created"

    status_update = client.patch(
        f"/jobs/{job_id}/status",
        json={"status": "applied"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert status_update.status_code == 200

    activities = client.get(
        f"/jobs/{job_id}/activities",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert len(activities.json()) == 2
    assert "saved" in activities.json()[1]["description"]
    assert "applied" in activities.json()[1]["description"]

    unauthenticated = client.get(f"/jobs/{job_id}")
    assert unauthenticated.status_code == 401

    cross_user = client.get(
        f"/jobs/{job_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert cross_user.status_code == 404

    foreign_activities = client.get(
        f"/jobs/{job_id}/activities",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert foreign_activities.status_code == 404

    foreign_company_job = client.post(
        "/jobs",
        json={
            "title": "Foreign Company Job",
            "company_id": company.json()["id"],
            "location": "Remote",
        },
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert foreign_company_job.status_code == 404

    in_use_delete = client.delete(
        f"/companies/{company.json()['id']}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert in_use_delete.status_code == 409

    unused_company = client.post(
        "/companies",
        json={"name": "Unused Company"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert unused_company.status_code == 201
    deleted = client.delete(
        f"/companies/{unused_company.json()['id']}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert deleted.status_code == 204


def test_company_routes_require_authentication(
    client: httpx.Client,
) -> None:
    response = client.get("/companies")

    assert response.status_code == 401


def test_readiness_endpoint_reports_available_dependencies(
    client: httpx.Client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ReadyRedis:
        def ping(self) -> bool:
            return True

    class ReadySession:
        def execute(self, statement: object) -> None:
            del statement
            return None

        def close(self) -> None:
            return None

    monkeypatch.setattr(health, "redis_client", ReadyRedis())
    monkeypatch.setattr(health, "SessionLocal", lambda: ReadySession())

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ready", "redis": "ready"},
    }


def test_interviews_are_crud_and_isolated_by_user(
    client: httpx.Client,
) -> None:
    owner_token = register_and_login(client, "interview-owner@example.com")
    other_token = register_and_login(client, "interview-other@example.com")
    company = client.post(
        "/companies",
        json={"name": "Interview Co"},
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()
    job = client.post(
        "/jobs",
        json={"title": "Engineer", "company_id": company["id"], "location": "Remote"},
        headers={"Authorization": f"Bearer {owner_token}"},
    ).json()
    payload = {
        "job_id": job["id"],
        "title": "Technical interview",
        "interview_type": "video",
        "interview_stage": "technical",
        "scheduled_at": "2099-01-02T10:00:00+00:00",
        "duration_minutes": 60,
    }

    created = client.post(
        "/interviews",
        json=payload,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert created.status_code == 201
    interview_id = created.json()["id"]

    upcoming = client.get(
        "/interviews/upcoming",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert upcoming.status_code == 200
    assert upcoming.json()[0]["id"] == interview_id

    hidden = client.get(
        f"/interviews/{interview_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert hidden.status_code == 404

    updated = client.patch(
        f"/interviews/{interview_id}",
        json={
            "scheduled_at": "2099-01-03T11:00:00+00:00",
            "outcome": "passed",
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert updated.status_code == 200
    assert updated.json()["outcome"] == "passed"

    invalid = client.post(
        "/interviews",
        json={**payload, "duration_minutes": 0},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert invalid.status_code == 422


def test_reminders_and_notifications_are_persistent_and_user_scoped(
    client: httpx.Client,
    db_session: Session,
) -> None:
    first_token = register_and_login(client, "reminder-one@example.com")
    second_token = register_and_login(client, "reminder-two@example.com")
    due_at = "2020-01-01T10:00:00+00:00"

    created = client.post(
        "/reminders",
        json={"title": "Follow up", "due_at": due_at},
        headers={"Authorization": f"Bearer {first_token}"},
    )
    assert created.status_code == 201
    reminder_id = created.json()["id"]

    assert client.get(
        f"/reminders/{reminder_id}",
        headers={"Authorization": f"Bearer {second_token}"},
    ).status_code == 404

    assert create_due_reminder_notifications(db_session) == 1
    notifications = client.get(
        "/notifications",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    assert notifications.status_code == 200
    assert len(notifications.json()) == 1
    assert notifications.json()[0]["read"] is False

    assert client.patch(
        "/notifications/read-all",
        headers={"Authorization": f"Bearer " + first_token},
    ).json() == {"unread_count": 0}
    assert client.get(
        "/notifications/unread-count",
        headers={"Authorization": f"Bearer {first_token}"},
    ).json() == {"unread_count": 0}


def test_document_upload_download_and_storage_permissions(
    client: httpx.Client,
    tmp_path: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_token = register_and_login(client, "documents-owner@example.com")
    storage_root = tmp_path / "documents"
    monkeypatch.setattr(phase2_module, "DOCUMENT_STORAGE_PATH", storage_root)

    upload = client.post(
        "/documents",
        files={"file": ("resume.txt", b"private resume", "text/plain")},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert upload.status_code == 201
    document = upload.json()
    user_directories = [path for path in storage_root.iterdir() if path.is_dir()]
    assert len(user_directories) == 1
    user_directory = user_directories[0]
    assert user_directory.is_dir()
    assert (user_directory / document["filename"]).exists() is False
    stored_files = list(user_directory.iterdir())
    assert len(stored_files) == 1
    assert stored_files[0].read_bytes() == b"private resume"
    assert user_directory.stat().st_mode & stat.S_IWUSR
    if sys.platform != "win32":
        assert not user_directory.stat().st_mode & stat.S_IWGRP
        assert not user_directory.stat().st_mode & stat.S_IWOTH

    download = client.get(
        f"/documents/{document['id']}/download",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert download.status_code == 200
    assert download.content == b"private resume"


def test_analytics_route_requires_authentication(client: httpx.Client) -> None:
    response = client.get("/analytics/summary")
    assert response.status_code == 401


def test_contacts_support_crud_search_and_ownership_validation(
    client: httpx.Client,
) -> None:
    owner_token = register_and_login(client, "contacts-owner@example.com")
    other_token = register_and_login(client, "contacts-other@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    owner_company = client.post(
        "/companies",
        json={"name": "Owner Company"},
        headers=owner_headers,
    )
    assert owner_company.status_code == 201
    owner_company_id = owner_company.json()["id"]
    other_company = client.post(
        "/companies",
        json={"name": "Other Company"},
        headers=other_headers,
    )
    assert other_company.status_code == 201
    other_job = client.post(
        "/jobs",
        json={
            "title": "Other User Job",
            "company_id": other_company.json()["id"],
            "location": "Remote",
        },
        headers=other_headers,
    )
    assert other_job.status_code == 201

    invalid_company = client.post(
        "/contacts",
        json={"name": "Invalid", "company_id": other_company.json()["id"]},
        headers=owner_headers,
    )
    assert invalid_company.status_code == 404

    invalid_job_reference = client.post(
        "/contacts",
        json={"name": "Invalid Job", "job_id": other_job.json()["id"]},
        headers=owner_headers,
    )
    assert invalid_job_reference.status_code == 404

    created = client.post(
        "/contacts",
        json={
            "name": "Recruiter",
            "email": "recruiter@example.com",
            "role": "Hiring Manager",
            "company_id": owner_company_id,
        },
        headers=owner_headers,
    )
    assert created.status_code == 201
    contact_id = created.json()["id"]

    listed = client.get(
        "/contacts?search=hiring",
        headers=owner_headers,
    )
    assert listed.status_code == 200
    assert [contact["id"] for contact in listed.json()] == [contact_id]

    detail = client.get(f"/contacts/{contact_id}", headers=owner_headers)
    assert detail.status_code == 200
    assert detail.json()["company_id"] == owner_company_id

    hidden = client.get(f"/contacts/{contact_id}", headers=other_headers)
    assert hidden.status_code == 404

    cross_user_update = client.patch(
        f"/contacts/{contact_id}",
        json={"name": "Changed"},
        headers=other_headers,
    )
    assert cross_user_update.status_code == 404

    invalid_update = client.patch(
        f"/contacts/{contact_id}",
        json={"company_id": other_company.json()["id"]},
        headers=owner_headers,
    )
    assert invalid_update.status_code == 404

    updated = client.patch(
        f"/contacts/{contact_id}",
        json={"name": "Updated Recruiter", "phone": "+1 555 0100"},
        headers=owner_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated Recruiter"

    cross_user_delete = client.delete(
        f"/contacts/{contact_id}",
        headers=other_headers,
    )
    assert cross_user_delete.status_code == 404

    deleted = client.delete(f"/contacts/{contact_id}", headers=owner_headers)
    assert deleted.status_code == 204
    assert client.get(f"/contacts/{contact_id}", headers=owner_headers).status_code == 404


def test_contacts_reject_missing_and_invalid_fields(client: httpx.Client) -> None:
    token = register_and_login(client, "contacts-validation@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    missing_name = client.post("/contacts", json={}, headers=headers)
    assert missing_name.status_code == 422

    invalid_email = client.post(
        "/contacts",
        json={"name": "Contact", "email": "not-an-email"},
        headers=headers,
    )
    assert invalid_email.status_code == 422

    invalid_job = client.post(
        "/contacts",
        json={"name": "Contact", "job_id": 999999},
        headers=headers,
    )
    assert invalid_job.status_code == 404
