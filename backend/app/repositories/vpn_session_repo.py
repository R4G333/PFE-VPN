from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.monitoring import SessionStatus, TrafficStat, VpnSession


def get_active_sessions(db: Session) -> list[VpnSession]:
    return (
        db.query(VpnSession)
        .filter(VpnSession.status == SessionStatus.ACTIVE)
        .order_by(VpnSession.connected_since.desc())
        .all()
    )


def get_session_by_common_name_and_real_address(
    db: Session, common_name: str, real_address: str, connected_since: datetime
) -> VpnSession | None:
    return (
        db.query(VpnSession)
        .filter(
            VpnSession.common_name == common_name,
            VpnSession.real_address == real_address,
            VpnSession.connected_since == connected_since,
            VpnSession.status == SessionStatus.ACTIVE,
        )
        .first()
    )


def create_session(
    db: Session,
    common_name: str,
    real_address: str,
    virtual_address: str | None,
    bytes_received: int,
    bytes_sent: int,
    connected_since: datetime,
) -> VpnSession:
    session = VpnSession(
        common_name=common_name,
        real_address=real_address,
        virtual_address=virtual_address,
        bytes_received=bytes_received,
        bytes_sent=bytes_sent,
        connected_since=connected_since,
        status=SessionStatus.ACTIVE,
        last_seen_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_session_traffic(
    db: Session, session: VpnSession, bytes_received: int, bytes_sent: int
) -> VpnSession:
    session.bytes_received = bytes_received
    session.bytes_sent = bytes_sent
    session.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


def mark_session_disconnected(db: Session, session: VpnSession) -> VpnSession:
    session.status = SessionStatus.DISCONNECTED
    session.disconnected_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


def add_traffic_snapshot(
    db: Session, session_id: str, bytes_received: int, bytes_sent: int
) -> TrafficStat:
    snap = TrafficStat(
        session_id=session_id,
        bytes_received=bytes_received,
        bytes_sent=bytes_sent,
        recorded_at=datetime.now(timezone.utc),
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


def get_recent_disconnects(db: Session, limit: int = 10) -> list[VpnSession]:
    return (
        db.query(VpnSession)
        .filter(VpnSession.status == SessionStatus.DISCONNECTED)
        .order_by(VpnSession.disconnected_at.desc())
        .limit(limit)
        .all()
    )


def count_connections_since(db: Session, since: datetime) -> int:
    return db.query(VpnSession).filter(VpnSession.connected_since >= since).count()


def get_traffic_timeseries(db: Session, since: datetime) -> list[tuple[datetime, int, int]]:
    """
    Aggregate bytes_received/bytes_sent across all sessions, grouped by
    recorded_at, since the given timestamp. Returns list of
    (recorded_at, total_bytes_received, total_bytes_sent).
    """
    rows = (
        db.query(
            TrafficStat.recorded_at,
            func.sum(TrafficStat.bytes_received),
            func.sum(TrafficStat.bytes_sent),
        )
        .filter(TrafficStat.recorded_at >= since)
        .group_by(TrafficStat.recorded_at)
        .order_by(TrafficStat.recorded_at.asc())
        .all()
    )
    return [(r[0], int(r[1] or 0), int(r[2] or 0)) for r in rows]


def get_total_traffic_since(db: Session, since: datetime) -> tuple[int, int]:
    """
    Sum of bytes_received / bytes_sent across the latest snapshot per
    session within the window (approximation: sums all snapshots' deltas
    isn't tracked, so we sum the max snapshot per session as cumulative).
    Simplified: sum the most recent snapshot per session in the window.
    """
    subq = (
        db.query(
            TrafficStat.session_id,
            func.max(TrafficStat.recorded_at).label("max_recorded"),
        )
        .filter(TrafficStat.recorded_at >= since)
        .group_by(TrafficStat.session_id)
        .subquery()
    )

    rows = (
        db.query(TrafficStat.bytes_received, TrafficStat.bytes_sent)
        .join(
            subq,
            (TrafficStat.session_id == subq.c.session_id)
            & (TrafficStat.recorded_at == subq.c.max_recorded),
        )
        .all()
    )
    total_recv = sum(r[0] for r in rows) if rows else 0
    total_sent = sum(r[1] for r in rows) if rows else 0
    return int(total_recv), int(total_sent)