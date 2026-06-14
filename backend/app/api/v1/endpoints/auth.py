"""Authentication endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.auth.service import (
    change_password as change_password_service,
    get_current_user_from_token,
    get_optional_user_from_token,
    login_user,
    refresh_token_pair,
    register_user,
    request_password_reset,
    reset_password as reset_password_service,
)
from app.models.user import User
from app.schemas.user import (
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    Token,
    UserCreate,
    UserResponse,
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Return the authenticated active user for bearer-token protected routes."""
    return get_current_user_from_token(db, token)


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Return the current user when a valid token exists, otherwise None."""
    return get_optional_user_from_token(db, token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Register a new email/password user."""
    return register_user(db, user_data=user_data, background_tasks=background_tasks)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login with email and password, returning access and refresh tokens."""
    return login_user(db, email=form_data.username, password=form_data.password)


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access and refresh tokens using a valid refresh token."""
    return refresh_token_pair(db, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user."""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout is client-side for stateless JWT; clients should discard tokens."""
    return {"message": "Successfully logged out"}


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the current user's password after confirming the existing password."""
    return change_password_service(db, user=current_user, request=request)


@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Request a password reset without revealing whether the email exists."""
    return request_password_reset(
        db,
        request=request,
        background_tasks=background_tasks,
    )


@router.post("/reset-password")
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db),
):
    """Reset a password with a valid password-reset token."""
    return reset_password_service(db, request=request)
