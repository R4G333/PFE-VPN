from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import require_analyst_or_admin, require_any_role
from app.db.session import get_db
from app.models.monitoring import EnforcementStatus
from app.models.user import ApplicationUser
from app.repositories import blocked_device_repo
from app.schemas.monitoring import (
    BlockedDeviceCreate,
    BlockedDeviceListResponse,
    BlockedDeviceResponse,
)
from app.services import monitoring_service

router = APIRouter(prefix="/blocked-devices", tags=["blocked-devices"])


@router.get(
    "",
    response_model=BlockedDeviceListResponse,
    summary="List blocked devices (active + history)",
)
def list_blocked_devices(
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: ApplicationUser = Depends(require_any_role),
):
    items = blocked_device_repo.get_devices(db, is_active=is_active, skip=skip, limit=limit)
    total = blocked_device_repo.count_devices(db, is_active=is_active)
    return BlockedDeviceListResponse(total=total, items=items)


@router.post(
    "",
    response_model=BlockedDeviceResponse,
    status_code=201,
    summary="Block an IP address (admin or analyst)",
)
def create_blocked_device(
    payload: BlockedDeviceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: ApplicationUser = Depends(require_analyst_or_admin),
):
    ip = request.client.host if request.client else None
    return monitoring_service.block_device(
        db=db,
        ip_address=payload.ip_address,
        reason=payload.reason,
        actor_username=current_user.username,
        alert_id=payload.alert_id,
        request_ip=ip,
    )


@router.post(
    "/{device_id}/unblock",
    response_model=BlockedDeviceResponse,
    summary="Unblock a previously blocked IP (admin or analyst)",
)
def unblock_blocked_device(
    device_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: ApplicationUser = Depends(require_analyst_or_admin),
):
    ip = request.client.host if request.client else None
    return monitoring_service.unblock_device(
        db=db,
        device_id=device_id,
        actor_username=current_user.username,
        request_ip=ip,
    )