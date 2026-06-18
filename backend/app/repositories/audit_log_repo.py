from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def create_log(
    db: Session,
    actor: str,
    action: str,
    target: str,
    detail: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    log = AuditLog(
        actor=actor,
        action=action,
        target=target,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_logs(
    db: Session,
    actor: str | None = None,
    action: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[AuditLog]:
    q = db.query(AuditLog)
    if actor:
        q = q.filter(AuditLog.actor == actor)
    if action:
        q = q.filter(AuditLog.action == action)
    return q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()


def count_logs(
    db: Session,
    actor: str | None = None,
    action: str | None = None,
) -> int:
    q = db.query(AuditLog)
    if actor:
        q = q.filter(AuditLog.actor == actor)
    if action:
        q = q.filter(AuditLog.action == action)
    return q.count()