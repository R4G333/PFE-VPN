from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.vpn_request import RequestStatus, VpnRequest


def create_request(db: Session, ad_username: str, display_name: str) -> VpnRequest:
    req = VpnRequest(
        ad_username=ad_username,
        display_name=display_name,
        status=RequestStatus.PENDING,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def get_request_by_id(db: Session, request_id: str) -> VpnRequest | None:
    return db.query(VpnRequest).filter(VpnRequest.id == request_id).first()


def get_requests(
    db: Session,
    status: RequestStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[VpnRequest]:
    q = db.query(VpnRequest)
    if status:
        q = q.filter(VpnRequest.status == status)
    return q.order_by(VpnRequest.created_at.desc()).offset(skip).limit(limit).all()


def count_requests(db: Session, status: RequestStatus | None = None) -> int:
    q = db.query(VpnRequest)
    if status:
        q = q.filter(VpnRequest.status == status)
    return q.count()


def approve_request(db: Session, req: VpnRequest, reviewed_by: str) -> VpnRequest:
    req.status = RequestStatus.APPROVED
    req.reviewed_by = reviewed_by
    req.reviewed_at = datetime.now(timezone.utc)
    req.rejection_reason = None
    db.commit()
    db.refresh(req)
    return req


def reject_request(
    db: Session, req: VpnRequest, reviewed_by: str, reason: str
) -> VpnRequest:
    req.status = RequestStatus.REJECTED
    req.reviewed_by = reviewed_by
    req.reviewed_at = datetime.now(timezone.utc)
    req.rejection_reason = reason
    db.commit()
    db.refresh(req)
    return req


def has_pending_or_approved_request(db: Session, ad_username: str) -> bool:
    return (
        db.query(VpnRequest)
        .filter(
            VpnRequest.ad_username == ad_username,
            VpnRequest.status.in_([RequestStatus.PENDING, RequestStatus.APPROVED]),
        )
        .first()
        is not None
    )