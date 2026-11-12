import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.redis import client as redis_client
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "message": "Job Tracker API is running",
    }


@router.get("/health/ready")
def readiness_check() -> JSONResponse:
    checks: dict[str, str] = {}

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ready"
    except SQLAlchemyError:
        logger.exception("Readiness database check failed")
        checks["database"] = "unavailable"
    finally:
        db.close()

    try:
        redis_client.ping()
        checks["redis"] = "ready"
    except RedisError:
        logger.exception("Readiness Redis check failed")
        checks["redis"] = "unavailable"

    is_ready = all(value == "ready" for value in checks.values())
    return JSONResponse(
        status_code=(
            status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
        ),
        content={
            "status": "ready" if is_ready else "unavailable",
            "checks": checks,
        },
    )
