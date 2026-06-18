#!/usr/bin/env python3
"""
collect_vpn_sessions.py

Parses /var/log/openvpn-status.log (OpenVPN status v2 format) and:
  - creates new VpnSession rows for newly-connected clients
  - updates bytes_received/bytes_sent + last_seen_at for active sessions
  - inserts a TrafficStat snapshot row for each active session
  - marks sessions as DISCONNECTED if they no longer appear in the status file

Intended to run via cron every 5-10 seconds:
    * * * * * /usr/bin/python3 /app/app/scripts/collect_vpn_sessions.py >> /var/log/vpn_collector.log 2>&1

(For sub-minute intervals, use a wrapper loop or systemd timer with
OnUnitActiveSec=5s instead of plain cron, which has a 1-minute resolution.)

Status file format (HEADER,CLIENT_LIST,...):
    Common Name, Real Address, Virtual Address, Virtual IPv6 Address,
    Bytes Received, Bytes Sent, Connected Since, Connected Since (time_t),
    Username, Client ID, Peer ID, Data Channel Cipher
"""
import logging
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.repositories import vpn_session_repo

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("collect_vpn_sessions")

settings = get_settings()


def parse_status_file(path: str) -> list[dict]:
    """
    Returns a list of dicts, one per CLIENT_LIST row:
      {common_name, real_address, virtual_address, bytes_received,
       bytes_sent, connected_since (datetime), connected_since_t (int)}
    """
    clients: list[dict] = []

    if not os.path.exists(path):
        logger.warning("Status file not found: %s", path)
        return clients

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("CLIENT_LIST"):
                continue

            parts = line.split(",")
            # CLIENT_LIST,Common Name,Real Address,Virtual Address,Virtual IPv6 Address,
            # Bytes Received,Bytes Sent,Connected Since,Connected Since (time_t),
            # Username,Client ID,Peer ID,Data Channel Cipher
            if len(parts) < 9:
                continue

            try:
                common_name = parts[1].strip()
                real_address = parts[2].strip().split(":")[0]  # strip port
                virtual_address = parts[3].strip() or None
                bytes_received = int(parts[5].strip())
                bytes_sent = int(parts[6].strip())
                connected_since_t = int(parts[8].strip())
                connected_since = datetime.fromtimestamp(connected_since_t, tz=timezone.utc)
            except (ValueError, IndexError) as exc:
                logger.warning("Failed to parse CLIENT_LIST line: %s (%s)", line, exc)
                continue

            clients.append(
                {
                    "common_name": common_name,
                    "real_address": real_address,
                    "virtual_address": virtual_address,
                    "bytes_received": bytes_received,
                    "bytes_sent": bytes_sent,
                    "connected_since": connected_since,
                }
            )

    return clients


def run():
    clients = parse_status_file(settings.OPENVPN_STATUS_LOG)
    logger.info("Parsed %d active client(s) from status file", len(clients))

    db = SessionLocal()
    try:
        # Build a set of "keys" present in this snapshot for disconnect detection
        seen_keys: set[tuple[str, str, datetime]] = set()

        for client in clients:
            key = (client["common_name"], client["real_address"], client["connected_since"])
            seen_keys.add(key)

            existing = vpn_session_repo.get_session_by_common_name_and_real_address(
                db,
                common_name=client["common_name"],
                real_address=client["real_address"],
                connected_since=client["connected_since"],
            )

            if existing:
                vpn_session_repo.update_session_traffic(
                    db,
                    existing,
                    bytes_received=client["bytes_received"],
                    bytes_sent=client["bytes_sent"],
                )
                session_id = existing.id
            else:
                created = vpn_session_repo.create_session(
                    db,
                    common_name=client["common_name"],
                    real_address=client["real_address"],
                    virtual_address=client["virtual_address"],
                    bytes_received=client["bytes_received"],
                    bytes_sent=client["bytes_sent"],
                    connected_since=client["connected_since"],
                )
                session_id = created.id
                logger.info(
                    "New session: %s from %s", client["common_name"], client["real_address"]
                )

            # Always record a traffic snapshot for time-series graphs
            vpn_session_repo.add_traffic_snapshot(
                db,
                session_id=session_id,
                bytes_received=client["bytes_received"],
                bytes_sent=client["bytes_sent"],
            )

        # Detect disconnects: any ACTIVE session not in this snapshot
        active_sessions = vpn_session_repo.get_active_sessions(db)
        for session in active_sessions:
            key = (session.common_name, session.real_address, session.connected_since)
            if key not in seen_keys:
                vpn_session_repo.mark_session_disconnected(db, session)
                logger.info(
                    "Session disconnected: %s from %s",
                    session.common_name,
                    session.real_address,
                )

    finally:
        db.close()


if __name__ == "__main__":
    run()