"""monitoring and security tables

Revision ID: 0002_monitoring
Revises: 0001_initial
Create Date: 2026-06-13 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_monitoring"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── vpn_sessions ─────────────────────────────────────────────────────────
    op.create_table(
        "vpn_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("common_name", sa.String(255), nullable=False),
        sa.Column("real_address", sa.String(64), nullable=False),
        sa.Column("virtual_address", sa.String(64), nullable=True),
        sa.Column("bytes_received", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("bytes_sent", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("connected_since", sa.DateTime(timezone=True), nullable=False),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "DISCONNECTED", name="sessionstatus"),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_vpn_sessions_common_name", "vpn_sessions", ["common_name"])
    op.create_index("ix_vpn_sessions_real_address", "vpn_sessions", ["real_address"])
    op.create_index("ix_vpn_sessions_status", "vpn_sessions", ["status"])

    # ── traffic_stats ────────────────────────────────────────────────────────
    op.create_table(
        "traffic_stats",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("vpn_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bytes_received", sa.BigInteger, nullable=False),
        sa.Column("bytes_sent", sa.BigInteger, nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_traffic_stats_session_id", "traffic_stats", ["session_id"])
    op.create_index("ix_traffic_stats_recorded_at", "traffic_stats", ["recorded_at"])

    # ── auth_events ──────────────────────────────────────────────────────────
    op.create_table(
        "auth_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("source_ip", sa.String(64), nullable=False),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_events_username", "auth_events", ["username"])
    op.create_index("ix_auth_events_source_ip", "auth_events", ["source_ip"])
    op.create_index("ix_auth_events_success", "auth_events", ["success"])
    op.create_index("ix_auth_events_event_time", "auth_events", ["event_time"])

    # ── security_alerts ──────────────────────────────────────────────────────
    op.create_table(
        "security_alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "alert_type",
            sa.Enum("BRUTE_FORCE", "PASSWORD_SPRAY", name="alerttype"),
            nullable=False,
        ),
        sa.Column("source_ip", sa.String(64), nullable=False),
        sa.Column("target_username", sa.String(255), nullable=True),
        sa.Column("occurrence_count", sa.Integer, nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("OPEN", "ACKNOWLEDGED", "RESOLVED", name="alertstatus"),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("resolved_by", sa.String(100), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_security_alerts_alert_type", "security_alerts", ["alert_type"])
    op.create_index("ix_security_alerts_source_ip", "security_alerts", ["source_ip"])
    op.create_index("ix_security_alerts_target_username", "security_alerts", ["target_username"])
    op.create_index("ix_security_alerts_status", "security_alerts", ["status"])
    op.create_index("ix_security_alerts_detected_at", "security_alerts", ["detected_at"])

    # ── blocked_devices ──────────────────────────────────────────────────────
    op.create_table(
        "blocked_devices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ip_address", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("blocked_by", sa.String(100), nullable=False),
        sa.Column("blocked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("unblocked_by", sa.String(100), nullable=True),
        sa.Column("unblocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "enforcement_status",
            sa.Enum("PENDING", "APPLIED", "FAILED", name="enforcementstatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("enforcement_error", sa.Text, nullable=True),
        sa.Column(
            "alert_id",
            sa.String(36),
            sa.ForeignKey("security_alerts.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_blocked_devices_ip_address", "blocked_devices", ["ip_address"])
    op.create_index("ix_blocked_devices_is_active", "blocked_devices", ["is_active"])
    op.create_index("ix_blocked_devices_enforcement_status", "blocked_devices", ["enforcement_status"])

    # ── script_state ─────────────────────────────────────────────────────────
    op.create_table(
        "script_state",
        sa.Column("script_name", sa.String(100), primary_key=True),
        sa.Column("last_position", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("script_state")
    op.drop_table("blocked_devices")
    op.drop_table("security_alerts")
    op.drop_table("auth_events")
    op.drop_table("traffic_stats")
    op.drop_table("vpn_sessions")
    op.execute("DROP TYPE IF EXISTS enforcementstatus")
    op.execute("DROP TYPE IF EXISTS alertstatus")
    op.execute("DROP TYPE IF EXISTS alerttype")
    op.execute("DROP TYPE IF EXISTS sessionstatus")