"""Shared account entitlement rules."""

from datetime import datetime, timezone

from app.models.user import User, UserRole


ACTIVE_SUBSCRIPTION_STATUSES = {
    "active",
    "manual",
    "trialing",
    "cancel_at_period_end",
}


def _to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def role_value(user: User | None) -> str | None:
    if user is None:
        return None
    return user.role.value if hasattr(user.role, "value") else str(user.role)


def has_active_subscription(user: User | None, *, now: datetime | None = None) -> bool:
    """Return whether the user's paid role is currently usable."""
    role = role_value(user)
    if role == UserRole.ADMIN.value:
        return True
    if role not in {UserRole.PRO.value, UserRole.ENTERPRISE.value} or user is None:
        return False

    status = (user.subscription_status or "").strip().lower()
    if status and status not in ACTIVE_SUBSCRIPTION_STATUSES:
        return False

    if user.subscription_end_date is None:
        return True

    end_date = _to_utc_naive(user.subscription_end_date)
    compare_at = _to_utc_naive(now) if now else datetime.utcnow()
    return end_date > compare_at


def effective_role(user: User | None, *, now: datetime | None = None) -> str | None:
    """Return the role that should be used for quota and feature decisions."""
    role = role_value(user)
    if role in {UserRole.PRO.value, UserRole.ENTERPRISE.value} and not has_active_subscription(
        user,
        now=now,
    ):
        return UserRole.FREE.value
    return role
