from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.monitoring import BlockedDevice, EnforcementStatus


def create_blocked_device(
    db: Session, ip_address: str, reason: str, blocked_by: str, alert_id: str | None = None
) -> BlockedDevice:
    device = BlockedDevice(
        ip_address=ip_address,
        reason=reason,
        blocked_by=blocked_by,
        blocked_at=datetime.now(timezone.utc),
        is_active=True,
        enforcement_status=EnforcementStatus.PENDING,
        alert_id=alert_id,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def get_device_by_id(db: Session, device_id: str) -> BlockedDevice | None:
    return db.query(BlockedDevice).filter(BlockedDevice.id == device_id).first()


def get_active_block_for_ip(db: Session, ip_address: str) -> BlockedDevice | None:
    return (
        db.query(BlockedDevice)
        .filter(BlockedDevice.ip_address == ip_address, BlockedDevice.is_active.is_(True))
        .first()
    )


def get_devices(
    db: Session,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[BlockedDevice]:
    q = db.query(BlockedDevice)
    if is_active is not None:
        q = q.filter(BlockedDevice.is_active == is_active)
    return q.order_by(BlockedDevice.blocked_at.desc()).offset(skip).limit(limit).all()


def count_devices(db: Session, is_active: bool | None = None) -> int:
    q = db.query(BlockedDevice)
    if is_active is not None:
        q = q.filter(BlockedDevice.is_active == is_active)
    return q.count()


def count_active(db: Session) -> int:
    return db.query(BlockedDevice).filter(BlockedDevice.is_active.is_(True)).count()


def unblock_device(db: Session, device: BlockedDevice, unblocked_by: str) -> BlockedDevice:
    device.is_active = False
    device.unblocked_by = unblocked_by
    device.unblocked_at = datetime.now(timezone.utc)
    device.enforcement_status = EnforcementStatus.PENDING  # enforce_ufw.py will remove the rule
    db.commit()
    db.refresh(device)
    return device


def get_pending_enforcement(db: Session) -> list[BlockedDevice]:
    return (
        db.query(BlockedDevice)
        .filter(BlockedDevice.enforcement_status == EnforcementStatus.PENDING)
        .all()
    )


def set_enforcement_status(
    db: Session, device: BlockedDevice, status: EnforcementStatus, error: str | None = None
) -> BlockedDevice:
    device.enforcement_status = status
    device.enforcement_error = error
    db.commit()
    db.refresh(device)
    return device