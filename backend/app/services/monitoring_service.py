"""
Monitoring / security service layer:
  - build_monitoring_overview() : aggregates dashboard data
  - list_vpn_group_members()    : AD VPN_Users members
  - revoke_vpn_access()         : remove user from AD group + audit
  - block_device() / unblock_device() : write intent for enforce_ufw.py
  - resolve_alert() / acknowledge_alert()
"""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.monitoring import AlertStatus, SecurityAlert
from app.repositories import (
    audit_log_repo,
    auth_event_repo,
    blocked_device_repo,
    security_alert_repo,
    vpn_session_repo,
)
from app.schemas.monitoring import (
    ActiveSession,
    MonitoringOverview,
    RecentDisconnect,
    TrafficPoint,
)
from app.services import ldap_service


# ─────────────────────────────────────────────────────────────────────────────
# Monitoring overview
# ─────────────────────────────────────────────────────────────────────────────

def build_monitoring_overview(db: Session) -> MonitoringOverview:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    day_start_24h = now - timedelta(hours=24)

    # AD VPN_Users group count (live)
    vpn_members = ldap_service.get_vpn_group_members()
    total_authorized = len(vpn_members)

    # Active sessions
    active = vpn_session_repo.get_active_sessions(db)
    active_sessions = [
        ActiveSession(
            common_name=s.common_name,
            real_address=s.real_address,
            virtual_address=s.virtual_address,
            bytes_received=s.bytes_received,
            bytes_sent=s.bytes_sent,
            connected_since=s.connected_since,
        )
        for s in active
    ]

    # Recent disconnects
    disconnects = vpn_session_repo.get_recent_disconnects(db, limit=10)
    recent_disconnects = [
        RecentDisconnect(
            common_name=s.common_name,
            real_address=s.real_address,
            disconnected_at=s.disconnected_at,
            bytes_received=s.bytes_received,
            bytes_sent=s.bytes_sent,
        )
        for s in disconnects
    ]

    # Connection counts
    connections_today = vpn_session_repo.count_connections_since(db, today_start)
    connections_this_week = vpn_session_repo.count_connections_since(db, week_start)

    # Traffic totals (24h) and timeseries
    total_recv, total_sent = vpn_session_repo.get_total_traffic_since(db, day_start_24h)
    timeseries_raw = vpn_session_repo.get_traffic_timeseries(db, day_start_24h)
    traffic_timeseries = [
        TrafficPoint(recorded_at=ts, bytes_received=br, bytes_sent=bs)
        for ts, br, bs in timeseries_raw
    ]

    # Failed auth attempts (24h)
    failed_24h = auth_event_repo.count_failed_since(db, day_start_24h)

    # Open alerts
    open_alerts = security_alert_repo.count_open(db)

    # Active blocked IPs
    active_blocks = blocked_device_repo.count_active(db)

    return MonitoringOverview(
        total_vpn_authorized_users=total_authorized,
        currently_connected=len(active_sessions),
        active_sessions=active_sessions,
        recent_disconnects=recent_disconnects,
        connections_today=connections_today,
        connections_this_week=connections_this_week,
        total_bytes_received_24h=total_recv,
        total_bytes_sent_24h=total_sent,
        traffic_timeseries=traffic_timeseries,
        failed_auth_attempts_24h=failed_24h,
        open_alerts_count=open_alerts,
        active_blocked_ips_count=active_blocks,
    )


# ─────────────────────────────────────────────────────────────────────────────
# VPN Users (AD group management)
# ─────────────────────────────────────────────────────────────────────────────

def list_vpn_group_members():
    return ldap_service.get_vpn_group_members()


def revoke_vpn_access(
    db: Session, sam_account: str, admin_username: str, ip_address: str | None = None
) -> None:
    """
    Remove a user from the VPN_Users AD group (admin only).
    """
    success = ldap_service.remove_user_from_vpn_group(sam_account)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to remove user from Active Directory VPN_Users group.",
        )

    audit_log_repo.create_log(
        db,
        actor=admin_username,
        action="ACCESS_REVOKED",
        target=sam_account,
        detail="Removed from VPN_Users AD group",
        ip_address=ip_address,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Blocked devices
# ─────────────────────────────────────────────────────────────────────────────

def block_device(
    db: Session,
    ip_address: str,
    reason: str,
    actor_username: str,
    alert_id: str | None = None,
    request_ip: str | None = None,
):
    existing = blocked_device_repo.get_active_block_for_ip(db, ip_address)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This IP address is already blocked",
        )

    device = blocked_device_repo.create_blocked_device(
        db, ip_address=ip_address, reason=reason, blocked_by=actor_username, alert_id=alert_id
    )

    audit_log_repo.create_log(
        db,
        actor=actor_username,
        action="DEVICE_BLOCKED",
        target=ip_address,
        detail=reason,
        ip_address=request_ip,
    )

    return device


def unblock_device(
    db: Session, device_id: str, actor_username: str, request_ip: str | None = None
):
    device = blocked_device_repo.get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blocked device not found")
    if not device.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device is not currently blocked")

    device = blocked_device_repo.unblock_device(db, device, unblocked_by=actor_username)

    audit_log_repo.create_log(
        db,
        actor=actor_username,
        action="DEVICE_UNBLOCKED",
        target=device.ip_address,
        detail=None,
        ip_address=request_ip,
    )

    return device


# ─────────────────────────────────────────────────────────────────────────────
# Security alerts
# ─────────────────────────────────────────────────────────────────────────────

def resolve_alert(
    db: Session, alert_id: str, actor_username: str, note: str | None, request_ip: str | None = None
) -> SecurityAlert:
    alert = security_alert_repo.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alert already resolved")

    alert = security_alert_repo.resolve_alert(db, alert, resolved_by=actor_username)

    audit_log_repo.create_log(
        db,
        actor=actor_username,
        action="ALERT_RESOLVED",
        target=f"{alert.alert_type}:{alert.source_ip}",
        detail=note,
        ip_address=request_ip,
    )

    return alert


def acknowledge_alert(db: Session, alert_id: str, actor_username: str) -> SecurityAlert:
    alert = security_alert_repo.get_alert_by_id(db, alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.status != AlertStatus.OPEN:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Alert is already {alert.status}")

    return security_alert_repo.acknowledge_alert(db, alert)