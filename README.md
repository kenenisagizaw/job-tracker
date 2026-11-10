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

The API exposes `/metrics` for Prometheus-compatible monitoring and `/health`
for liveness checks. Run `scripts\scan-image.ps1` with Trivy before deployment;
the script fails on unfixed high or critical vulnerabilities.

PostgreSQL and Redis are attached only to the internal `backend` network.
Only the API is exposed through the frontend network.

Keep `SECRET_KEY`, database credentials, SMTP credentials, and migration
credentials in a secret manager or `.env`; `.env` is excluded from Git and the
Docker build context. If a secret is exposed, rotate it before deployment.
For Docker secrets, mount the JWT key and set `SECRET_KEY_FILE`.

Jobs use `company_id` to reference the related row in `companies`. The company filter searches the related company's name.

After model changes, create and apply an Alembic migration:

```powershell
alembic revision --autogenerate -m "add companies and job relationship"
alembic upgrade head
```

## Endpoints

- `GET /health`
- `GET /jobs?status=saved&location=Remote`
- `POST /jobs` (provide `company_id`)
- `GET /jobs/{job_id}`
- `PUT /jobs/{job_id}`
- `PATCH /jobs/{job_id}/status`
- `DELETE /jobs/{job_id}`
