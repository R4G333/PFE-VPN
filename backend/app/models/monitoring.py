import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ─────────────────────────────────────────────────────────────────────────────
# VPN Sessions (from openvpn-status.log)
# ─────────────────────────────────────────────────────────────────────────────

class SessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISCONNECTED = "DISCONNECTED"


class VpnSession(Base):
    __tablename__ = "vpn_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    common_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    real_address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    virtual_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    bytes_received: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    bytes_sent: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    connected_since: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), nullable=False, default=SessionStatus.ACTIVE, index=True
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    traffic_stats: Mapped[list["TrafficStat"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<VpnSession {self.common_name} [{self.status}]>"


# ─────────────────────────────────────────────────────────────────────────────
# Traffic stats (time-series snapshots per session per collector run)
# ─────────────────────────────────────────────────────────────────────────────

class TrafficStat(Base):
    __tablename__ = "traffic_stats"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vpn_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bytes_received: Mapped[int] = mapped_column(BigInteger, nullable=False)
    bytes_sent: Mapped[int] = mapped_column(BigInteger, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    session: Mapped["VpnSession"] = relationship(back_populates="traffic_stats")

    def __repr__(self) -> str:
        return f"<TrafficStat session={self.session_id} @ {self.recorded_at}>"


# ─────────────────────────────────────────────────────────────────────────────
# Auth events (from /var/log/auth.log via pam_sss)
# ─────────────────────────────────────────────────────────────────────────────

class AuthEvent(Base):
    __tablename__ = "auth_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_ip: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<AuthEvent {self.username}@{self.source_ip} success={self.success}>"


# ─────────────────────────────────────────────────────────────────────────────
# Security alerts (brute force / password spraying)
# ─────────────────────────────────────────────────────────────────────────────

class AlertType(str, enum.Enum):
    BRUTE_FORCE = "BRUTE_FORCE"
    PASSWORD_SPRAY = "PASSWORD_SPRAY"


class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType), nullable=False, index=True)
    source_ip: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_username: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False)

    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus), nullable=False, default=AlertStatus.OPEN, index=True
    )
    resolved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    def __repr__(self) -> str:
        return f"<SecurityAlert {self.alert_type} {self.source_ip} [{self.status}]>"


# ─────────────────────────────────────────────────────────────────────────────
# Blocked devices (IP-based, enforced via ufw by enforce_ufw.py)
# ─────────────────────────────────────────────────────────────────────────────

class EnforcementStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPLIED = "APPLIED"
    FAILED = "FAILED"


class BlockedDevice(Base):
    __tablename__ = "blocked_devices"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    blocked_by: Mapped[str] = mapped_column(String(100), nullable=False)
    blocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    unblocked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unblocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    enforcement_status: Mapped[EnforcementStatus] = mapped_column(
        Enum(EnforcementStatus), nullable=False, default=EnforcementStatus.PENDING, index=True
    )
    enforcement_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    alert_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("security_alerts.id", ondelete="SET NULL"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<BlockedDevice {self.ip_address} active={self.is_active}>"


# ─────────────────────────────────────────────────────────────────────────────
# Script state (generic offset tracking for collector scripts)
# ─────────────────────────────────────────────────────────────────────────────

class ScriptState(Base):
    __tablename__ = "script_state"

    script_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    last_position: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<ScriptState {self.script_name} = {self.last_position}>"