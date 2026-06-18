from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import ApplicationUser
from app.schemas.monitoring import MonitoringOverview
from app.services import monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get(
    "/overview",
    response_model=MonitoringOverview,
    summary="Dashboard overview: connected users, traffic, alerts",
)
def get_overview(
    db: Session = Depends(get_db),
    _: ApplicationUser = Depends(get_current_user),
):
    return monitoring_service.build_monitoring_overview(db)