from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import ApplicationUser, Role
from app.repositories.user_repo import get_user_by_username

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> ApplicationUser:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if not username:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = get_user_by_username(db, username)
    if user is None or not user.is_active:
        raise credentials_exc
    return user


def require_roles(*roles: Role):
    """
    Factory that returns a dependency enforcing one of the given roles.
    """
    def _checker(current_user: ApplicationUser = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return _checker


# Convenience role dependencies
require_admin = require_roles(Role.ADMIN)
require_analyst_or_admin = require_roles(Role.ADMIN, Role.SECURITY_ANALYST)
require_any_role = require_roles(Role.ADMIN, Role.SECURITY_ANALYST, Role.AUDITOR)
