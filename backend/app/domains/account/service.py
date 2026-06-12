"""Account domain logic.

Endpoints should stay thin: auth and request/response wiring live in the API
layer, while account statistics and profile mutations live here.
"""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import UsageLog, User
from app.schemas.user import UserUpdate


def _role_value(user: User) -> str:
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def get_usage_stats(db: Session, user: User) -> dict[str, int | str]:
    """Return trusted usage counters for the current account."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    total_requests = db.query(func.count(UsageLog.id)).filter(
        UsageLog.user_id == user.id
    ).scalar() or 0

    requests_today = db.query(func.count(UsageLog.id)).filter(
        UsageLog.user_id == user.id,
        UsageLog.created_at >= today_start,
    ).scalar() or 0

    storage_used = db.query(func.sum(UsageLog.file_size)).filter(
        UsageLog.user_id == user.id,
        UsageLog.file_size.isnot(None),
    ).scalar() or 0

    role = _role_value(user)
    if role == "free":
        quota_limit = settings.RATE_LIMIT_FREE
        quota_remaining = max(0, quota_limit - int(requests_today))
    else:
        quota_limit = -1
        quota_remaining = -1

    return {
        "total_requests": int(total_requests),
        "requests_today": int(requests_today),
        "storage_used": int(storage_used),
        "quota_remaining": quota_remaining,
        "quota_limit": quota_limit,
        "role": role,
    }


def update_account(db: Session, user: User, payload: UserUpdate) -> User:
    """Apply profile updates for the current account."""
    if payload.full_name is not None:
        user.full_name = payload.full_name

    if payload.password is not None:
        user.hashed_password = get_password_hash(payload.password)

    db.commit()
    db.refresh(user)
    return user


def delete_account(db: Session, user: User) -> None:
    """Delete the current account and related rows through ORM cascades."""
    db.delete(user)
    db.commit()
