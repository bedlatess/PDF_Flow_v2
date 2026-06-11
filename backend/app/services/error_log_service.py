"""Local API error logging for the hidden control room."""
from __future__ import annotations

import traceback
import uuid
from typing import Optional

from fastapi import Request

from app.core.database import SessionLocal, get_db
from app.models.user import ApiErrorLog


def _client_host(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


def _truncate(value: Optional[str], limit: int) -> Optional[str]:
    if value is None:
        return None
    if len(value) <= limit:
        return value
    return f"{value[:limit - 3]}..."


def log_api_error(
    request: Request,
    status_code: int,
    error: Exception | None = None,
    error_message: str | None = None,
) -> None:
    """Persist a compact error summary without request bodies or file content."""
    if request.url.path.startswith("/api/v1/admin/errors"):
        return

    override = getattr(request.app, "dependency_overrides", {}).get(get_db)
    db_generator = override() if override else None
    db = next(db_generator) if db_generator else SessionLocal()
    try:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        user_id = getattr(request.state, "user_id", None)
        traceback_summary = None
        error_type = None
        message = error_message

        if error:
            error_type = error.__class__.__name__
            message = message or str(error)
            traceback_summary = "".join(traceback.format_exception_only(type(error), error)).strip()

        db.add(ApiErrorLog(
            user_id=user_id,
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            query_string=_truncate(str(request.url.query), 1200) if request.url.query else None,
            status_code=status_code,
            error_type=_truncate(error_type, 120),
            error_message=_truncate(message, 2000),
            traceback_summary=_truncate(traceback_summary, 2000),
            ip_address=_client_host(request),
            user_agent=_truncate(request.headers.get("user-agent"), 1000),
        ))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        if db_generator:
            try:
                next(db_generator)
            except StopIteration:
                pass
        else:
            db.close()
