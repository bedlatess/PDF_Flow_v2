"""Core email/password authentication domain."""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import secrets
from urllib.parse import urlencode

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import PasswordResetToken, User, UserRole
from app.schemas.user import PasswordResetConfirm, PasswordResetRequest, UserCreate
from app.services.email_service import email_service


def credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def parse_token_user_id(token: str, *, expected_type: str | None = None) -> int | None:
    payload = decode_token(token)
    if payload is None:
        return None
    if expected_type is not None and payload.get("type") != expected_type:
        return None
    user_id = payload.get("sub")
    try:
        return int(user_id)
    except (ValueError, TypeError):
        return None


def get_current_user_from_token(db: Session, token: str | None) -> User:
    if not token:
        raise credentials_exception()

    user_id = parse_token_user_id(token)
    if user_id is None:
        raise credentials_exception()

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def get_optional_user_from_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None

    try:
        return get_current_user_from_token(db, token)
    except HTTPException:
        return None


def token_pair_for_user(user: User) -> dict:
    return {
        "access_token": create_access_token(data={"sub": user.id}),
        "refresh_token": create_refresh_token(data={"sub": user.id}),
        "token_type": "bearer",
    }


def hash_password_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_password_reset_link_token(
    db: Session,
    *,
    user: User,
    source: str = "user_request",
    admin: User | None = None,
) -> tuple[str, datetime]:
    expires_at = datetime.utcnow() + timedelta(
        hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS
    )
    token = secrets.token_urlsafe(48)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_password_reset_token(token),
            source=source,
            created_by_admin_id=admin.id if admin else None,
            expires_at=expires_at,
        )
    )
    return token, expires_at


def consume_password_reset_link_token(db: Session, *, token: str) -> User | None:
    token_hash = hash_password_reset_token(token)
    record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )
    if record is None:
        return None
    if record.used_at is not None or record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    record.used_at = datetime.utcnow()
    return user


def oauth_callback_redirect_url(*, frontend_url: str, token_pair: dict) -> str:
    query = urlencode({
        "access_token": token_pair["access_token"],
        "refresh_token": token_pair["refresh_token"],
        "token_type": token_pair.get("token_type", "bearer"),
    })
    return f"{frontend_url}/auth/oauth-callback?{query}"


def oauth_error_redirect_url(*, frontend_url: str, provider: str) -> str:
    query = urlencode({"error": "oauth_failed", "provider": provider})
    return f"{frontend_url}/auth/login?{query}"


def oauth_link_result_redirect_url(*, frontend_url: str, success: bool) -> str:
    return f"{frontend_url}/profile?oauth_linked={'success' if success else 'error'}"


def get_or_create_oauth_user(
    db: Session,
    *,
    provider: str,
    oauth_id: str,
    email: str,
    full_name: str | None = None,
) -> User:
    user = db.query(User).filter(
        User.oauth_provider == provider,
        User.oauth_id == oauth_id,
    ).first()

    if user:
        user.last_login_at = datetime.utcnow()
        db.commit()
        return user

    user = db.query(User).filter(User.email == email).first()

    if user:
        user.oauth_provider = provider
        user.oauth_id = oauth_id
        user.is_verified = True
        user.last_login_at = datetime.utcnow()
        db.commit()
        return user

    random_password = secrets.token_urlsafe(32)
    new_user = User(
        email=email,
        hashed_password=get_password_hash(random_password),
        full_name=full_name,
        oauth_provider=provider,
        oauth_id=oauth_id,
        role=UserRole.FREE,
        is_active=True,
        is_verified=True,
        last_login_at=datetime.utcnow(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def link_oauth_identity(
    db: Session,
    *,
    user: User,
    provider: str,
    oauth_id: str,
) -> User:
    existing_oauth_user = db.query(User).filter(
        User.oauth_provider == provider,
        User.oauth_id == oauth_id,
        User.id != user.id,
    ).first()

    if existing_oauth_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This {provider} account is already linked to another user",
        )

    user.oauth_provider = provider
    user.oauth_id = oauth_id
    db.commit()
    db.refresh(user)
    return user


def register_user(
    db: Session,
    *,
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
) -> User:
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=UserRole.FREE,
        is_active=True,
        is_verified=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    background_tasks.add_task(
        email_service.send_welcome_email,
        to=new_user.email,
        username=new_user.full_name or new_user.email.split("@")[0],
    )

    return new_user


def login_user(db: Session, *, email: str, password: str) -> dict:
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    user.last_login_at = datetime.utcnow()
    db.commit()

    return token_pair_for_user(user)


def refresh_token_pair(db: Session, *, refresh_token: str) -> dict:
    user_id = parse_token_user_id(refresh_token, expected_type="refresh")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
        )

    return token_pair_for_user(user)


def request_password_reset(
    db: Session,
    *,
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    user = db.query(User).filter(User.email == request.email).first()

    if user and user.is_active:
        reset_token, _expires_at = create_password_reset_link_token(db, user=user)
        db.commit()

        background_tasks.add_task(
            email_service.send_password_reset_email,
            to=user.email,
            username=user.full_name or user.email.split("@")[0],
            reset_token=reset_token,
        )

    return {
        "message": "If an account exists with that email, a password reset link has been sent"
    }


def reset_password(db: Session, *, request: PasswordResetConfirm) -> dict:
    user = consume_password_reset_link_token(db, token=request.token)
    if user is None:
        user_id = parse_token_user_id(request.token, expected_type="password_reset")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token",
            )

    user.hashed_password = get_password_hash(request.new_password)
    db.commit()

    return {"message": "Password successfully reset"}
