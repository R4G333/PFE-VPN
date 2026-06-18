from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import require_analyst_or_admin, require_any_role
from app.db.session import get_db
from app.models.monitoring import AlertStatus
from app.models.user import ApplicationUser
from app.repositories import security_alert_repo
from app.schemas.monitoring import (
    AlertResolve,
    SecurityAlertListResponse,
    SecurityAlertResponse,
)
from app.services import monitoring_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get(
    "",
    response_model=SecurityAlertListResponse,
    summary="List security alerts (brute force / password spraying)",
)
def list_alerts(
    status_filter: AlertStatus | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: ApplicationUser = Depends(require_any_role),
):
    items = security_alert_repo.get_alerts(db, status=status_filter, skip=skip, limit=limit)
    total = security_alert_repo.count_alerts(db, status=status_filter)
    return SecurityAlertListResponse(total=total, items=items)


@router.post(
    "/{alert_id}/resolve",
    response_model=SecurityAlertResponse,
    summary="Mark an alert as resolved (admin or analyst)",
)
def resolve_alert(
    alert_id: str,
    payload: AlertResolve,
    request: Request,
    db: Session = Depends(get_db),
    current_user: ApplicationUser = Depends(require_analyst_or_admin),
):
    ip = request.client.host if request.client else None
    return monitoring_service.resolve_alert(
        db=db,
        alert_id=alert_id,
        actor_username=current_user.username,
        note=payload.note,
        request_ip=ip,
    )


@router.post(
    "/{alert_id}/acknowledge",
    response_model=SecurityAlertResponse,
    summary="Acknowledge an alert (admin or analyst)",
)
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: ApplicationUser = Depends(require_analyst_or_admin),
):
    return monitoring_service.acknowledge_alert(
        db=db,
        alert_id=alert_id,
        actor_username=current_user.username,
    )