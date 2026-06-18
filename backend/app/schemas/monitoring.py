from datetime import datetime

from pydantic import BaseModel, Field

from app.models.monitoring import AlertStatus, AlertType, EnforcementStatus, SessionStatus


# ─────────────────────────────────────────────────────────────────────────────
# Monitoring overview
# ─────────────────────────────────────────────────────────────────────────────

class ActiveSession(BaseModel):
    model_config = {"from_attributes": True}

    common_name: str
    real_address: str
    virtual_address: str | None
    bytes_received: int
    bytes_sent: int
    connected_since: datetime


class TrafficPoint(BaseModel):
    recorded_at: datetime
    bytes_received: int
    bytes_sent: int


class RecentDisconnect(BaseModel):
    common_name: str
    real_address: str
    disconnected_at: datetime | None
    bytes_received: int
    bytes_sent: int


class MonitoringOverview(BaseModel):
    total_vpn_authorized_users: int
    currently_connected: int
    active_sessions: list[ActiveSession]
    recent_disconnects: list[RecentDisconnect]

    connections_today: int
    connections_this_week: int

    total_bytes_received_24h: int
    total_bytes_sent_24h: int

    traffic_timeseries: list[TrafficPoint]

    failed_auth_attempts_24h: int
    open_alerts_count: int
    active_blocked_ips_count: int


# ─────────────────────────────────────────────────────────────────────────────
# VPN Users (AD group management)
# ─────────────────────────────────────────────────────────────────────────────

class VpnUserResponse(BaseModel):
    sam_account: str
    display_name: str


# ─────────────────────────────────────────────────────────────────────────────
# Blocked devices
# ─────────────────────────────────────────────────────────────────────────────

class BlockedDeviceCreate(BaseModel):
    ip_address: str = Field(..., min_length=1, max_length=64)
    reason: str = Field(..., min_length=1, max_length=1000)
    alert_id: str | None = None


class BlockedDeviceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    ip_address: str
    reason: str
    blocked_by: str
    blocked_at: datetime
    is_active: bool
    unblocked_by: str | None
    unblocked_at: datetime | None
    enforcement_status: EnforcementStatus
    enforcement_error: str | None
    alert_id: str | None


class BlockedDeviceListResponse(BaseModel):
    total: int
    items: list[BlockedDeviceResponse]


# ─────────────────────────────────────────────────────────────────────────────
# Security alerts
# ─────────────────────────────────────────────────────────────────────────────

class AlertResolve(BaseModel):
    note: str | None = Field(None, max_length=1000)


class SecurityAlertResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    alert_type: AlertType
    source_ip: str
    target_username: str | None
    occurrence_count: int
    window_start: datetime
    window_end: datetime
    status: AlertStatus
    resolved_by: str | None
    resolved_at: datetime | None
    detected_at: datetime


class SecurityAlertListResponse(BaseModel):
    total: int
    items: list[SecurityAlertResponse]