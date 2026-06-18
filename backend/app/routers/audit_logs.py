from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_any_role
from app.db.session import get_db
from app.models.user import ApplicationUser
from app.repositories import audit_log_repo
from app.schemas.audit_log import AuditLogListResponse

router = APIRouter(prefix="/logs", tags=["audit-logs"])


@router.get("", response_model=AuditLogListResponse, summary="View audit logs")
def get_logs(
    actor: str | None = None,
    action: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: ApplicationUser = Depends(require_any_role),
):
    items = audit_log_repo.get_logs(db, actor=actor, action=action, skip=skip, limit=limit)
    total = audit_log_repo.count_logs(db, actor=actor, action=action)
    return AuditLogListResponse(total=total, items=items)