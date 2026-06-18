from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.monitoring import AuthEvent


def create_event(
    db: Session, username: str, source_ip: str, success: bool, event_time: datetime
) -> AuthEvent:
    event = AuthEvent(
        username=username,
        source_ip=source_ip,
        success=success,
        event_time=event_time,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def bulk_create_events(db: Session, events: list[dict]) -> int:
    """
    Bulk insert auth events. Each dict needs: username, source_ip, success, event_time.
    Returns the number of rows inserted.
    """
    if not events:
        return 0
    objs = [
        AuthEvent(
            username=e["username"],
            source_ip=e["source_ip"],
            success=e["success"],
            event_time=e["event_time"],
        )
        for e in events
    ]
    db.bulk_save_objects(objs)
    db.commit()
    return len(objs)


def count_failed_since(db: Session, since: datetime) -> int:
    return (
        db.query(AuthEvent)
        .filter(AuthEvent.success.is_(False), AuthEvent.event_time >= since)
        .count()
    )


def get_failed_events_since(db: Session, since: datetime) -> list[AuthEvent]:
    return (
        db.query(AuthEvent)
        .filter(AuthEvent.success.is_(False), AuthEvent.event_time >= since)
        .order_by(AuthEvent.event_time.asc())
        .all()
    )