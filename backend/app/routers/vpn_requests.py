from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin, require_analyst_or_admin
from app.db.session import get_db
from app.models.user import ApplicationUser
from app.models.vpn_request import RequestStatus
from app.repositories import vpn_request_repo
from app.schemas.vpn_request import (
    VpnRequestCreate,
    VpnRequestListResponse,
    VpnRequestReject,
    VpnRequestResponse,
)
from app.services import vpn_service

router = APIRouter(tags=["vpn-requests"])


# ── Public: submit a VPN access request ──────────────────────────────────────

@router.post(
    "/vpn/request",
    response_model=VpnRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a VPN access request (AD credentials required)",
)
def submit_request(
    payload: VpnRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return vpn_service.submit_vpn_request(
        db=db,
        ad_username=payload.ad_username,
        ad_password=payload.ad_password,
        ip_address=ip,
    )


# ── Authenticated: list and detail ───────────────────────────────────────────

@router.get(
    "/requests",
    response_model=VpnRequestListResponse,
    summary="List VPN requests (analyst/admin)",
)
def list_requests(
    status_filter: RequestStatus | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: ApplicationUser = Depends(require_analyst_or_admin),
):
    items = vpn_request_repo.get_requests(db, status=status_filter, skip=skip, limit=limit)
    total = vpn_request_repo.count_requests(db, status=status_filter)
    return VpnRequestListResponse(total=total, items=items)


@router.get(
    "/requests/{request_id}",
    response_model=VpnRequestResponse,
    summary="Get request details",
)
def get_request(
    request_id: str,
    db: Session = Depends(get_db),
    _: ApplicationUser = Depends(require_analyst_or_admin),
):
    from fastapi import HTTPException
    req = vpn_request_repo.get_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


# ── Analyst / Admin: approve or reject ───────────────────────────────────────

@router.post(
    "/requests/{request_id}/approve",
    response_model=VpnRequestResponse,
    summary="Approve a VPN request and add user to AD group",
)
def approve_request(
    request_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: ApplicationUser = Depends(require_admin),
):
    ip = request.client.host if request.client else None
    return vpn_service.approve_vpn_request(
        db=db,
        request_id=request_id,
        analyst_username=current_user.username,
        ip_address=ip,
    )


@router.post(
    "/requests/{request_id}/reject",
    response_model=VpnRequestResponse,
    summary="Reject a VPN request",
)
def reject_request(
    request_id: str,
    payload: VpnRequestReject,
    request: Request,
    db: Session = Depends(get_db),
    current_user: ApplicationUser = Depends(require_admin),
):
    ip = request.client.host if request.client else None
    return vpn_service.reject_vpn_request(
        db=db,
        request_id=request_id,
        analyst_username=current_user.username,
        reason=payload.rejection_reason,
        ip_address=ip,
    )