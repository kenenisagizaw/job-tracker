from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardMetrics
from app.services.dashboard_service import get_dashboard_metrics

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
def dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardMetrics:
    return get_dashboard_metrics(db, current_user)
