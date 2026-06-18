#!/usr/bin/env python3
"""
collect_auth_events.py

Tails /var/log/auth.log from the last processed byte offset (stored in
the script_state table) and extracts pam_sss authentication
success/failure events, inserting them into auth_events.

Only lines matching:
    pam_sss(login:auth): authentication (success|failure); ... rhost=<ip> user=<user>
are parsed. pam_unix lines are ignored (they're always followed by the
authoritative pam_sss result for SSSD-backed PAM stacks).

Example lines:
  2026-06-13T13:16:16.104217+01:00 ubuntu2404 openvpn: pam_sss(login:auth):
    authentication failure; logname= uid=0 euid=0 tty= ruser= rhost=192.168.182.131 user=ysf@hightech.local
  2026-06-13T13:16:26.553582+01:00 ubuntu2404 openvpn: pam_sss(login: auth):
    authentication success; logname= uid=0 euid=0 tty= ruser= rhost=192.168.182.131 user=ysf@hightech.local

Intended to run via cron / systemd timer every 5-10 seconds:
    * * * * * /usr/bin/python3 /app/app/scripts/collect_auth_events.py >> /var/log/auth_collector.log 2>&1
"""
import logging
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.repositories import auth_event_repo, script_state_repo

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("collect_auth_events")

settings = get_settings()

SCRIPT_NAME = "collect_auth_events"

# Matches the syslog timestamp prefix: 2026-06-13T13:16:16.104217+01:00
TIMESTAMP_RE = re.compile(r"^(\S+)\s")

# Matches pam_sss auth result lines (note: "login: auth" sometimes has a space after the colon)
PAM_SSS_RE = re.compile(
    r"pam_sss\(login:\s*auth\):\s*authentication (success|failure);.*?rhost=(\S+).*?user=(\S+)"
)


def parse_line(line: str) -> dict | None:
    """
    Returns {username, source_ip, success, event_time} or None if the line
    doesn't match a pam_sss auth result.
    """
    match = PAM_SSS_RE.search(line)
    if not match:
        return None

    result, rhost, user = match.groups()

    ts_match = TIMESTAMP_RE.match(line)
    if not ts_match:
        return None

    try:
        event_time = datetime.fromisoformat(ts_match.group(1))
    except ValueError:
        return None

    # Clean up trailing artifacts like "local" split across lines, stray dots
    user = user.strip().rstrip(".")

    return {
        "username": user,
        "source_ip": rhost.strip(),
        "success": result == "success",
        "event_time": event_time,
    }


def run():
    path = settings.AUTH_LOG
    if not os.path.exists(path):
        logger.warning("Auth log not found: %s", path)
        return

    db = SessionLocal()
    try:
        last_position_str = script_state_repo.get_state(db, SCRIPT_NAME)
        last_position = int(last_position_str) if last_position_str else 0

        file_size = os.path.getsize(path)

        # If the log was rotated/truncated, restart from the beginning
        if last_position > file_size:
            logger.info("Detected log rotation/truncation, restarting from 0")
            last_position = 0

        events: list[dict] = []

        with open(path, "r", errors="replace") as f:
            f.seek(last_position)
            for line in f:
                parsed = parse_line(line)
                if parsed:
                    events.append(parsed)
            new_position = f.tell()

        inserted = auth_event_repo.bulk_create_events(db, events)
        script_state_repo.set_state(db, SCRIPT_NAME, str(new_position))

        if inserted:
            logger.info("Inserted %d auth event(s)", inserted)
        else:
            logger.debug("No new auth events")

    finally:
        db.close()


if __name__ == "__main__":
    run()