import logging
import time
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import auth, health, metrics
from app.core.logging import configure_logging
from app.core.config import (
    APP_NAME,
    CORS_ORIGINS,
    DEADLINE_REMINDER_INTERVAL_SECONDS,
)
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY
from app import models
from app.routers.jobs import router as jobs_router
from app.routers.companies import router as companies_router
from app.routers.dashboard import router as dashboard_router
from app.routers.interviews import job_interviews_router, router as interviews_router
from app.routers.phase2 import router as phase2_router
from app.routers.analytics import router as analytics_router
from app.db.database import SessionLocal
from app.services.deadline_reminder_service import (
    create_due_reminder_notifications,
    send_due_deadline_reminders,
)

configure_logging()
logger = logging.getLogger(__name__)

async def deadline_reminder_loop() -> None:
    while True:
        try:
            db = SessionLocal()
            try:
                send_due_deadline_reminders(db)
                create_due_reminder_notifications(db)
            finally:
                db.close()
        except Exception:
            logger.exception("Deadline reminder job failed")
        await asyncio.sleep(DEADLINE_REMINDER_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(deadline_reminder_loop())
    try:
        yield
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


app = FastAPI(
    title=APP_NAME,
    description="API for managing jobs",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(companies_router)
app.include_router(dashboard_router)
app.include_router(interviews_router)
app.include_router(job_interviews_router)
app.include_router(phase2_router)
app.include_router(analytics_router)
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(metrics.router)


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    started = time.perf_counter()
    path = request.url.path
    try:
        response = await call_next(request)
        path = getattr(request.scope.get("route"), "path", path)
    except Exception:
        logger.exception("Unhandled request error")
        REQUEST_COUNT.labels(request.method, path, "500").inc()
        raise
    finally:
        REQUEST_LATENCY.labels(
            request.method,
            path,
        ).observe(time.perf_counter() - started)
    REQUEST_COUNT.labels(
        request.method,
        path,
        str(response.status_code),
    ).inc()
    return response


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception("Unhandled application error")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/", tags=["health"])
def home() -> dict[str, str]:
    return {"message": "Welcome to Job Tracker API", "status": "running"}
