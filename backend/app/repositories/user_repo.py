from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import ApplicationUser, Role
from app.schemas.user import UserCreate


def get_user_by_id(db: Session, user_id: str) -> ApplicationUser | None:
    return db.query(ApplicationUser).filter(ApplicationUser.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> ApplicationUser | None:
    return db.query(ApplicationUser).filter(ApplicationUser.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 50) -> list[ApplicationUser]:
    return db.query(ApplicationUser).offset(skip).limit(limit).all()


def count_users(db: Session) -> int:
    return db.query(ApplicationUser).count()


def create_user(db: Session, payload: UserCreate) -> ApplicationUser:
    user = ApplicationUser(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user_role(db: Session, user: ApplicationUser, role: Role) -> ApplicationUser:
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def set_user_active(db: Session, user: ApplicationUser, active: bool) -> ApplicationUser:
    user.is_active = active
    db.commit()
    db.refresh(user)
    return user