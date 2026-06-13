"""File endpoint orchestration domain."""

from __future__ import annotations

from datetime import datetime
import logging
import os
from typing import Awaitable, Callable

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.domains.account.entitlements import effective_role
from app.models.user import ProcessingJob, User, UserRole
from app.services.feature_gate import require_feature_access

ALLOWED_OFFICE_EXTENSIONS = {".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt"}
logger = logging.getLogger(__name__)


def user_upload_tier(user: User | None) -> str:
    if user is None:
        return UserRole.FREE.value

    role_value = effective_role(user) or UserRole.FREE.value
    if role_value == UserRole.ADMIN.value:
        return UserRole.ENTERPRISE.value
    return role_value


def validate_office_upload(file: UploadFile) -> str:
    filename = file.filename or ""
    extension = os.path.splitext(filename)[1].lower()
    if extension not in ALLOWED_OFFICE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_OFFICE_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {allowed}",
        )
    return extension


def require_file_feature(
    db: Session,
    feature_key: str,
    user: User | None,
) -> None:
    require_feature_access(db, feature_key, user)


def require_job_status(job_id: str, status_data: dict | None) -> dict:
    if not status_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )
    return status_data


def sync_cancelled_processing_job(db: Session, job_id: str) -> ProcessingJob | None:
    db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
    if db_job and db_job.status not in ("completed", "failed", "cancelled"):
        db_job.status = "cancelled"
        db_job.error_message = "Job cancelled by user"
        db_job.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(db_job)
    return db_job


async def run_file_operation(
    operation: Callable[[], Awaitable[dict]],
    *,
    error_detail: str,
    log_message: str,
) -> dict:
    try:
        return await operation()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("%s: %s", log_message, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        ) from exc
