# Job Tracker API

FastAPI service for creating, updating, filtering, and deleting PostgreSQL-backed jobs.

## Run locally

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation.

Set `DATABASE_URL` in `.env` to a PostgreSQL connection string. Passwords must remain in `.env` or another secret manager, never in source code.

## Production operations

The container runs `alembic upgrade head` before starting the API. A failed
migration prevents the application from starting.

PostgreSQL data is stored in the `postgres_data` named volume. Create backups
with `scripts\backup-postgres.ps1` and copy them to durable off-host storage.
Test restoring backups regularly; the volume is not a backup.

The API exposes `/metrics` for Prometheus-compatible monitoring, `/health` for
liveness checks, and `/health/ready` for PostgreSQL and Redis readiness checks.
Run `scripts\scan-image.ps1` with Trivy before deployment;
the script fails on unfixed high or critical vulnerabilities.

PostgreSQL and Redis are attached only to the internal `backend` network.
Only the API is exposed through the frontend network.

Keep `SECRET_KEY`, database credentials, SMTP credentials, and migration
credentials in a secret manager or `.env`; `.env` is excluded from Git and the
Docker build context. If a secret is exposed, rotate it before deployment.
For Docker secrets, mount the JWT key and set `SECRET_KEY_FILE`.

Jobs use `company_id` to reference the related row in `companies`. The company filter searches the related company's name.
Companies are private to the authenticated user; users may create companies with
the same name without sharing company records.

After model changes, create and apply an Alembic migration:

```powershell
alembic revision --autogenerate -m "add companies and job relationship"
alembic upgrade head
```

Interview management is available through the authenticated `/interviews` API.
It supports owner-scoped creation, filtering, upcoming interviews, rescheduling,
outcome updates, deletion, and the job-specific
`/jobs/{job_id}/interviews` listing. The web client exposes the same workflow at
`/interviews`.

Phase 2 also provides owner-scoped documents, contacts, reminders, notifications,
and analytics:

- `POST/GET/DELETE /documents` stores allowed uploads under the configured local storage path.
- `POST/GET/PATCH /contacts` manages private recruiter contacts.
- `POST/GET /reminders` and `PATCH /reminders/{id}/complete` manage follow-ups.
- `GET /notifications` and `PATCH /notifications/{id}/read` manage notification state.
- `GET /analytics/summary` returns application, interview, offer, and conversion metrics.

The frontend exposes these workflows at `/documents`, `/contacts`, `/reminders`,
and `/analytics`.

### Persistent document storage

The API container runs as the non-root `appuser` with UID/GID `10001:10001`.
Documents are stored under the absolute path `/app/storage`, backed by the
dedicated Docker volume `document_storage`. The image creates `/app/storage` with owner `appuser:appgroup` and mode `0750`;
the one-shot `storage-init` Compose service also repairs ownership on an
existing document volume before the API starts. No world-writable permissions
are required.

Deploy or update the service without removing volumes:

```powershell
docker compose up -d --build api
docker compose ps
```

Verify the effective user, mount, ownership, and write access:

```powershell
docker compose exec api id
docker compose exec api sh -c "findmnt -T /app/storage || true; stat -c '%U:%G %a %n' /app/storage; touch /app/storage/.write-test && rm /app/storage/.write-test"
docker volume inspect job-tracker-api_document_storage
```

If documents already exist in the old container filesystem or a host directory,
copy them to a verified host backup before recreating the API container. Replace
`careertrack-api-legacy` with the actual old container name from
`docker ps -a`:

```powershell
docker compose stop api
$backup = Join-Path (Get-Location) "document-storage-backup"
New-Item -ItemType Directory -Force $backup
docker cp careertrack-api-legacy:/app/storage/. $backup
Get-ChildItem -Force $backup
docker run --rm `
  -v job-tracker-api_document_storage:/app/storage `
  -v "${backup}:/backup:ro" `
  busybox sh -c "cp -a /backup/. /app/storage/"
docker compose up -d api
```

Inspect the source and destination listings before copying, and do not run the
copy if they are already the same volume. Never remove `postgres_data`,
`redis_data`, or `document_storage` as part of this migration.

## Endpoints

- `GET /health`
- `GET /health/ready`
- `GET /dashboard/metrics`
- `GET /jobs?status=saved&location=Remote`
- `POST /jobs` (provide `company_id`)
- `GET /jobs/{job_id}`
- `GET /jobs/{job_id}/activities`
- `PUT /jobs/{job_id}`
- `PATCH /jobs/{job_id}/status`
- `DELETE /jobs/{job_id}`
