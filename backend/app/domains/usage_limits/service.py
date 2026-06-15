"""Centralized tool access, quota checks, and conversion usage logs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import logging

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.domains.account.entitlements import has_active_subscription
from app.models.user import FeatureFlag, ToolUsageLog, User
from app.services.feature_gate import require_feature_access

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolUsageContext:
    feature_key: str
    user_id: int | None
    anonymous_key: str | None
    is_pro: bool
    daily_limit: int | None
    max_file_size_mb: int | None
    batch_file_limit: int | None


def anonymous_key_for_request(request: Request | None) -> str | None:
    if request is None:
        return None
    client_host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    digest = hashlib.sha256(f"{client_host}|{user_agent}".encode("utf-8")).hexdigest()
    return digest[:32]


def _positive_or_none(value: int | None) -> int | None:
    if value is None or value <= 0:
        return None
    return value


def _quota_for_flag(flag: FeatureFlag | None, user: User | None) -> tuple[bool, int | None, int | None, int | None]:
    is_pro = has_active_subscription(user)
    if flag is None:
        return is_pro, None, None, None
    if is_pro and flag.pro_unlimited:
        return is_pro, None, None, None
    if is_pro:
        return (
            True,
            _positive_or_none(flag.pro_daily_limit),
            _positive_or_none(flag.pro_max_file_size_mb),
            _positive_or_none(flag.pro_batch_file_limit),
        )
    return (
        False,
        _positive_or_none(flag.free_daily_limit),
        _positive_or_none(flag.free_max_file_size_mb),
        _positive_or_none(flag.free_batch_file_limit),
    )


def _daily_usage_count(
    db: Session,
    *,
    user_id: int | None,
    anonymous_key: str | None,
    tool_type: str,
    now: datetime,
) -> int:
    start = datetime(now.year, now.month, now.day)
    query = db.query(ToolUsageLog).filter(
        ToolUsageLog.tool_type == tool_type,
        ToolUsageLog.success == True,  # noqa: E712
        ToolUsageLog.created_at >= start,
        ToolUsageLog.created_at < start + timedelta(days=1),
    )
    if user_id is not None:
        query = query.filter(ToolUsageLog.user_id == user_id)
    else:
        query = query.filter(ToolUsageLog.user_id.is_(None), ToolUsageLog.anonymous_key == anonymous_key)
    return int(query.count())


def enforce_tool_access_and_limits(
    db: Session,
    *,
    feature_key: str,
    current_user: User | None,
    request: Request | None = None,
    file_sizes: list[int] | None = None,
    batch_count: int = 1,
    now: datetime | None = None,
) -> ToolUsageContext:
    """Enforce feature gate plus configured quota limits for task creation."""
    flag = require_feature_access(db, feature_key, current_user)
    return enforce_tool_limits_for_flag(
        db,
        feature_key=feature_key,
        flag=flag,
        current_user=current_user,
        request=request,
        file_sizes=file_sizes,
        batch_count=batch_count,
        now=now,
    )


def enforce_tool_limits_for_flag(
    db: Session,
    *,
    feature_key: str,
    flag: FeatureFlag | None,
    current_user: User | None,
    request: Request | None = None,
    file_sizes: list[int] | None = None,
    batch_count: int = 1,
    now: datetime | None = None,
) -> ToolUsageContext:
    """Enforce configured quota limits after feature access has already passed."""
    is_pro, daily_limit, max_file_size_mb, batch_file_limit = _quota_for_flag(flag, current_user)
    user_id = current_user.id if current_user else None
    anonymous_key = None if user_id is not None else anonymous_key_for_request(request)

    if batch_file_limit is not None and batch_count > batch_file_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This tool allows up to {batch_file_limit} files per batch for your current plan.",
        )

    sizes = file_sizes or []
    max_file_size_bytes = max_file_size_mb * 1024 * 1024 if max_file_size_mb is not None else None
    if max_file_size_bytes is not None and any(size > max_file_size_bytes for size in sizes):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Your current plan allows files up to {max_file_size_mb} MB for this tool.",
        )

    if daily_limit is not None:
        used_today = _daily_usage_count(
            db,
            user_id=user_id,
            anonymous_key=anonymous_key,
            tool_type=feature_key,
            now=now or datetime.utcnow(),
        )
        if used_today >= daily_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Daily conversion limit reached for this tool ({daily_limit}/day). Upgrade or try again tomorrow.",
            )

    return ToolUsageContext(
        feature_key=feature_key,
        user_id=user_id,
        anonymous_key=anonymous_key,
        is_pro=is_pro,
        daily_limit=daily_limit,
        max_file_size_mb=max_file_size_mb,
        batch_file_limit=batch_file_limit,
    )


def record_tool_usage(
    db: Session | None,
    *,
    context: ToolUsageContext | None,
    job_id: str | None,
    file_size: int = 0,
    file_count: int = 1,
    request: Request | None = None,
    success: bool = True,
    error_message: str | None = None,
) -> None:
    """Best-effort conversion usage record after a task has been created."""
    if db is None or context is None:
        return
    try:
        db.add(
            ToolUsageLog(
                user_id=context.user_id,
                anonymous_key=context.anonymous_key,
                tool_type=context.feature_key,
                job_id=job_id,
                file_size=file_size,
                file_count=file_count,
                success=success,
                error_message=(error_message or "")[:500] or None,
                ip_address=request.client.host if request and request.client else None,
                user_agent=(request.headers.get("user-agent", "")[:500] if request else None),
            )
        )
        db.commit()
    except Exception:
        logger.warning("Tool usage record failed for %s/%s", context.feature_key, job_id, exc_info=True)
        db.rollback()
