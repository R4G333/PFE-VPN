"""
VPN request workflow:
  submit_vpn_request()  — authenticate with AD, create PENDING request
  approve_vpn_request() — add user to AD group, update status
  reject_vpn_request()  — update status with reason
"""
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.vpn_request import RequestStatus, VpnRequest
from app.repositories import audit_log_repo, vpn_request_repo
from app.services import ldap_service

logger = logging.getLogger(__name__)


def submit_vpn_request(
    db: Session,
    ad_username: str,
    ad_password: str,
    ip_address: str | None = None,
) -> VpnRequest:
    """
    1. Validate AD credentials via LDAP bind.
    2. Guard against duplicate active requests.
    3. Create a PENDING request and audit log.
    """
    # Normalise: ensure UPN format
    if "@" not in ad_username:
        from app.core.config import get_settings
        ad_username = f"{ad_username}@{get_settings().LDAP_DOMAIN}"

    # Step 1: authenticate — password used here only, never stored
    authenticated = ldap_service.authenticate_user(ad_username, ad_password)
    if not authenticated:
        audit_log_repo.create_log(
            db,
            actor=ad_username,
            action="REQUEST_AUTH_FAILED",
            target="VPN_ACCESS",
            detail="LDAP bind failed",
            ip_address=ip_address,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Active Directory credentials",
        )

    # Step 2: prevent duplicate requests
    if vpn_request_repo.has_pending_or_approved_request(db, ad_username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active or pending VPN request already exists for this account",
        )

    # Step 3: fetch display name (best-effort)
    display_name = ldap_service.get_user_display_name(ad_username)

    # Step 4: persist request
    req = vpn_request_repo.create_request(db, ad_username, display_name)

    # Step 5: audit trail
    audit_log_repo.create_log(
        db,
        actor=ad_username,
        action="REQUEST_CREATED",
        target="VPN_ACCESS",
        detail=f"Request ID: {req.id}",
        ip_address=ip_address,
    )

    return req


def approve_vpn_request(
    db: Session,
    request_id: str,
    analyst_username: str,
    ip_address: str | None = None,
) -> VpnRequest:
    """
    1. Verify request exists and is PENDING.
    2. Add user to AD VPN_Users group.
    3. Update request status and write audit log.
    """
    req = vpn_request_repo.get_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if req.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is already {req.status}",
        )

    # Add to AD group
    success = ldap_service.add_user_to_vpn_group(req.ad_username)
    if not success:
        logger.error("Failed to add %s to VPN_Users during approval", req.ad_username)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to add user to Active Directory VPN group. Please check LDAP connectivity.",
        )

    req = vpn_request_repo.approve_request(db, req, analyst_username)

    audit_log_repo.create_log(
        db,
        actor=analyst_username,
        action="REQUEST_APPROVED",
        target=req.ad_username,
        detail=f"Request ID: {req.id}",
        ip_address=ip_address,
    )

    return req


def reject_vpn_request(
    db: Session,
    request_id: str,
    analyst_username: str,
    reason: str,
    ip_address: str | None = None,
) -> VpnRequest:
    req = vpn_request_repo.get_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if req.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request is already {req.status}",
        )

    req = vpn_request_repo.reject_request(db, req, analyst_username, reason)

    audit_log_repo.create_log(
        db,
        actor=analyst_username,
        action="REQUEST_REJECTED",
        target=req.ad_username,
        detail=f"Request ID: {req.id} | Reason: {reason}",
        ip_address=ip_address,
    )

    return req