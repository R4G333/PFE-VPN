from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.monitoring import AlertStatus, AlertType, SecurityAlert


def create_alert(
    db: Session,
    alert_type: AlertType,
    source_ip: str,
    target_username: str | None,
    occurrence_count: int,
    window_start: datetime,
    window_end: datetime,
) -> SecurityAlert:
    alert = SecurityAlert(
        alert_type=alert_type,
        source_ip=source_ip,
        target_username=target_username,
        occurrence_count=occurrence_count,
        window_start=window_start,
        window_end=window_end,
        status=AlertStatus.OPEN,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_alert_by_id(db: Session, alert_id: str) -> SecurityAlert | None:
    return db.query(SecurityAlert).filter(SecurityAlert.id == alert_id).first()


def get_alerts(
    db: Session,
    status: AlertStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[SecurityAlert]:
    q = db.query(SecurityAlert)
    if status:
        q = q.filter(SecurityAlert.status == status)
    return q.order_by(SecurityAlert.detected_at.desc()).offset(skip).limit(limit).all()


def count_alerts(db: Session, status: AlertStatus | None = None) -> int:
    q = db.query(SecurityAlert)
    if status:
        q = q.filter(SecurityAlert.status == status)
    return q.count()


def count_open(db: Session) -> int:
    return db.query(SecurityAlert).filter(SecurityAlert.status == AlertStatus.OPEN).count()


def resolve_alert(db: Session, alert: SecurityAlert, resolved_by: str) -> SecurityAlert:
    alert.status = AlertStatus.RESOLVED
    alert.resolved_by = resolved_by
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert


def acknowledge_alert(db: Session, alert: SecurityAlert) -> SecurityAlert:
    alert.status = AlertStatus.ACKNOWLEDGED
    db.commit()
    db.refresh(alert)
    return alert


def find_existing_open_alert(
    db: Session,
    alert_type: AlertType,
    source_ip: str,
    target_username: str | None,
    window_start: datetime,
) -> SecurityAlert | None:
    """
    Avoid duplicate alerts for the same ongoing incident: check for an OPEN
    alert of the same type/source/target whose window overlaps.
    """
    q = db.query(SecurityAlert).filter(
        SecurityAlert.alert_type == alert_type,
        SecurityAlert.source_ip == source_ip,
        SecurityAlert.status == AlertStatus.OPEN,
        SecurityAlert.window_end >= window_start,
    )
    if target_username is not None:
        q = q.filter(SecurityAlert.target_username == target_username)
    return q.first()