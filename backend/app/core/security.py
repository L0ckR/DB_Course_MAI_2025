import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.deps import get_db
from app.models.models import User

_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_MAX_PASSWORD_BYTES = 72
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/token")


def hash_password(password: str) -> str:
    return _password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _password_context.verify(password, password_hash)


def validate_password_length(password: str) -> None:
    if len(password.encode("utf-8")) > _MAX_PASSWORD_BYTES:
        raise ValueError("Password exceeds 72 bytes")


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.jwt_expires_minutes)
    payload = {
        "sub": str(user.user_id),
        "email": user.email,
        "iat": now,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc


def _set_audit_user(db: Session, user_id: uuid.UUID) -> None:
    db.execute(
        text("SELECT set_config('app.user_id', :user_id, true)"),
        {"user_id": str(user_id)},
    )


def get_current_user(
    request: Request,
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = _decode_access_token(token)
    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user_id = uuid.UUID(user_id_raw)
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )
    _set_audit_user(db, user.user_id)
    request.state.user_id = user.user_id
    return user
