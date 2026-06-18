#!/usr/bin/env python3
"""
detect_alerts.py

Analyzes recent auth_events to detect:
  - BRUTE_FORCE:    >= BRUTE_FORCE_THRESHOLD failed attempts for the SAME
                    username (from same or different source IPs) within
                    BRUTE_FORCE_WINDOW_SECONDS.
  - PASSWORD_SPRAY: >= SPRAY_THRESHOLD failed attempts from the SAME
                    source_ip across >= SPRAY_MIN_USERNAMES distinct
                    usernames within SPRAY_WINDOW_SECONDS.

Deduplicates against existing OPEN alerts for the same
type/source/target with an overlapping window, so repeated runs don't
spam duplicate alerts for an ongoing incident.

Intended to run via cron / systemd timer every 10-30 seconds:
    * * * * * /usr/bin/python3 /app/app/scripts/detect_alerts.py >> /var/log/alert_detector.log 2>&1
"""
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.monitoring import AlertType
from app.repositories import auth_event_repo, security_alert_repo

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("detect_alerts")

settings = get_settings()


def detect_brute_force(db, events: list) -> int:
    """
    Group failed events by username; for each username, check if any
    sliding window of BRUTE_FORCE_WINDOW_SECONDS contains
    >= BRUTE_FORCE_THRESHOLD events.
    """
    threshold = settings.BRUTE_FORCE_THRESHOLD
    window = timedelta(seconds=settings.BRUTE_FORCE_WINDOW_SECONDS)

    by_user: dict[str, list] = defaultdict(list)
    for e in events:
        by_user[e.username].append(e)

    created = 0
    for username, user_events in by_user.items():
        user_events.sort(key=lambda e: e.event_time)
        if len(user_events) < threshold:
            continue

        # Sliding window check
        for i in range(len(user_events) - threshold + 1):
            window_events = user_events[i : i + threshold]
            start = window_events[0].event_time
            end = window_events[-1].event_time
            if end - start <= window:
                # Use the source_ip of the most recent event as representative
                source_ip = window_events[-1].source_ip

                existing = security_alert_repo.find_existing_open_alert(
                    db,
                    alert_type=AlertType.BRUTE_FORCE,
                    source_ip=source_ip,
                    target_username=username,
                    window_start=start,
                )
                if existing:
                    continue

                security_alert_repo.create_alert(
                    db,
                    alert_type=AlertType.BRUTE_FORCE,
                    source_ip=source_ip,
                    target_username=username,
                    occurrence_count=len(window_events),
                    window_start=start,
                    window_end=end,
                )
                logger.info(
                    "BRUTE_FORCE alert: user=%s source_ip=%s count=%d window=%s..%s",
                    username, source_ip, len(window_events), start, end,
                )
                created += 1
                break  # one alert per username per run is enough

    return created


def detect_password_spray(db, events: list) -> int:
    """
    Group failed events by source_ip; for each IP, check if any sliding
    window of SPRAY_WINDOW_SECONDS contains >= SPRAY_THRESHOLD events
    across >= SPRAY_MIN_USERNAMES distinct usernames.
    """
    threshold = settings.SPRAY_THRESHOLD
    min_usernames = settings.SPRAY_MIN_USERNAMES
    window = timedelta(seconds=settings.SPRAY_WINDOW_SECONDS)

    by_ip: dict[str, list] = defaultdict(list)
    for e in events:
        by_ip[e.source_ip].append(e)

    created = 0
    for source_ip, ip_events in by_ip.items():
        ip_events.sort(key=lambda e: e.event_time)
        if len(ip_events) < threshold:
            continue

        for i in range(len(ip_events) - threshold + 1):
            window_events = ip_events[i : i + threshold]
            start = window_events[0].event_time
            end = window_events[-1].event_time
            if end - start > window:
                continue

            distinct_users = {e.username for e in window_events}
            if len(distinct_users) < min_usernames:
                continue

            existing = security_alert_repo.find_existing_open_alert(
                db,
                alert_type=AlertType.PASSWORD_SPRAY,
                source_ip=source_ip,
                target_username=None,
                window_start=start,
            )
            if existing:
                continue

            security_alert_repo.create_alert(
                db,
                alert_type=AlertType.PASSWORD_SPRAY,
                source_ip=source_ip,
                target_username=None,
                occurrence_count=len(window_events),
                window_start=start,
                window_end=end,
            )
            logger.info(
                "PASSWORD_SPRAY alert: source_ip=%s users=%d count=%d window=%s..%s",
                source_ip, len(distinct_users), len(window_events), start, end,
            )
            created += 1
            break  # one alert per source_ip per run is enough

    return created


def run():
    db = SessionLocal()
    try:
        # Look back over a window slightly larger than the largest detection
        # window, to catch incidents that span the boundary between runs.
        lookback_seconds = max(
            settings.BRUTE_FORCE_WINDOW_SECONDS, settings.SPRAY_WINDOW_SECONDS
        ) * 2
        since = datetime.now(timezone.utc) - timedelta(seconds=lookback_seconds)

        events = auth_event_repo.get_failed_events_since(db, since)
        if not events:
            logger.debug("No failed auth events in lookback window")
            return

        bf_count = detect_brute_force(db, events)
        spray_count = detect_password_spray(db, events)

        if bf_count or spray_count:
            logger.info(
                "Created %d brute-force and %d password-spray alert(s)",
                bf_count, spray_count,
            )

    finally:
        db.close()


if __name__ == "__main__":
    run()