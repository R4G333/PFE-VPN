from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin, require_analyst_or_admin
from app.db.session import get_db
from app.models.user import ApplicationUser
from app.schemas.monitoring import VpnUserResponse
from app.services import monitoring_service

router = APIRouter(prefix="/vpn-users", tags=["vpn-users"])


@router.get(
    "",
    response_model=list[VpnUserResponse],
    summary="List current VPN_Users AD group members",
)
def list_vpn_users(
    _: ApplicationUser = Depends(require_analyst_or_admin),
):
    members = monitoring_service.list_vpn_group_members()
    return [
        VpnUserResponse(sam_account=m.sam_account, display_name=m.display_name)
        for m in members
    ]


@router.delete(
    "/{sam_account}",
    status_code=204,
    summary="Revoke VPN access by removing the user from VPN_Users (admin only)",
)
def revoke_vpn_user(
    sam_account: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: ApplicationUser = Depends(require_admin),
):
    ip = request.client.host if request.client else None
    monitoring_service.revoke_vpn_access(
        db=db,
        sam_account=sam_account,
        admin_username=current_user.username,
        ip_address=ip,
    )