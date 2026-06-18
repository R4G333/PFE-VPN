#!/usr/bin/env python3
"""
enforce_ufw.py

Reads blocked_devices rows where enforcement_status='PENDING' and applies
the corresponding ufw rule:
  - is_active=True  -> ufw insert 1 deny from <ip> to any   (block)
  - is_active=False -> ufw delete deny from <ip> to any     (unblock)

On success, sets enforcement_status='APPLIED'.
On failure, sets enforcement_status='FAILED' and stores stderr in
enforcement_error.

This script must run with sufficient privileges to execute `ufw`
(e.g. via a narrowly-scoped sudoers entry for the UFW_BIN path only).
It is intentionally separate from the FastAPI process for security
isolation — the backend only writes "intent" rows to the DB.

Intended to run via cron / systemd timer every 5-10 seconds:
    * * * * * /usr/bin/python3 /app/app/scripts/enforce_ufw.py >> /var/log/ufw_enforcer.log 2>&1

Example sudoers entry (visudo):
    appuser ALL=(root) NOPASSWD: /usr/sbin/ufw insert 1 deny from * to any
    appuser ALL=(root) NOPASSWD: /usr/sbin/ufw delete deny from * to any
"""
import logging
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.monitoring import EnforcementStatus
from app.repositories import blocked_device_repo

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("enforce_ufw")

settings = get_settings()


def run_ufw(args: list[str]) -> tuple[bool, str]:
    """
    Run a ufw command via sudo. Returns (success, output_or_error).
    """
    cmd = ["sudo", settings.UFW_BIN] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, (result.stderr.strip() or result.stdout.strip())
    except subprocess.TimeoutExpired:
        return False, "ufw command timed out"
    except Exception as exc:
        return False, str(exc)


def run():
    db = SessionLocal()
    try:
        pending = blocked_device_repo.get_pending_enforcement(db)
        if not pending:
            logger.debug("No pending enforcement actions")
            return

        logger.info("Processing %d pending enforcement action(s)", len(pending))

        for device in pending:
            ip = device.ip_address

            if device.is_active:
                # Block: insert deny rule at top of chain
                ok, output = run_ufw(["insert", "1", "deny", "from", ip, "to", "any"])
                action = "block"
            else:
                # Unblock: remove deny rule
                ok, output = run_ufw(["delete", "deny", "from", ip, "to", "any"])
                action = "unblock"

            if ok:
                blocked_device_repo.set_enforcement_status(
                    db, device, EnforcementStatus.APPLIED, error=None
                )
                logger.info("Applied ufw %s for %s: %s", action, ip, output)
            else:
                blocked_device_repo.set_enforcement_status(
                    db, device, EnforcementStatus.FAILED, error=output
                )
                logger.error("Failed to %s %s via ufw: %s", action, ip, output)

    finally:
        db.close()


if __name__ == "__main__":
    run()