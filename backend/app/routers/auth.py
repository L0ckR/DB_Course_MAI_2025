from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    validate_password_length,
    verify_password,
)
from app.db.deps import get_db
from app.models.models import User
from app.schemas.auth import AuthLogin, AuthRegister, AuthSession, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthSession, status_code=status.HTTP_201_CREATED)
def register(payload: AuthRegister, db: Session = Depends(get_db)) -> AuthSession:
    try:
        validate_password_length(payload.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user)
    return {
        "user_id": user.user_id,
        "email": user.email,
        "full_name": user.full_name,
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=AuthSession)
def login(payload: AuthLogin, db: Session = Depends(get_db)) -> AuthSession:
    try:
        validate_password_length(payload.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )
    token = create_access_token(user)
    return {
        "user_id": user.user_id,
        "email": user.email,
        "full_name": user.full_name,
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/token", response_model=Token)
def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    try:
        validate_password_length(form_data.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    user = db.scalar(select(User).where(User.email == form_data.username))
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}
