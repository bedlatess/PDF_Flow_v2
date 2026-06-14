"""Job lifecycle service and compatibility helpers."""

from __future__ import annotations

from datetime import datetime
import time
from typing import Any, Mapping

from app.domains.jobs.repository import ProcessingJobRepository
from app.domains.jobs.types import (
    JobStatus,
    celery_state_to_job_status,
    is_terminal_job_status,
    normalize_job_status,
)
from app.models.user import ProcessingJob


JOB_TYPE_MESSAGE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("ocr", "ocr_pdf"),
    ("text", "ocr_pdf"),
    ("office", "office_to_pdf"),
    ("merge", "merge_pdf"),
    ("split", "split_pdf"),
    ("compression", "compress_pdf"),
    ("compress", "compress_pdf"),
    ("rotation", "rotate_pdf"),
    ("rotate", "rotate_pdf"),
    ("image to pdf", "image_to_pdf"),
    ("pdf to images", "pdf_to_image"),
)


class JobService:
    """Use-case boundary for durable processing jobs.

    R1 keeps existing Redis/Celery behavior intact. This service is intentionally
    small so later phases can move selected flows onto durable DB jobs.
    """

    def __init__(self, repository: ProcessingJobRepository):
        self.repository = repository

    def get(self, job_id: str) -> ProcessingJob | None:
        return self.repository.get_by_job_id(job_id)

    def create_pending(
        self,
        *,
        job_id: str,
        user_id: int,
        job_type: str,
        input_file_name: str,
        input_file_size: int,
    ) -> ProcessingJob:
        return self.repository.create(
            job_id=job_id,
            user_id=user_id,
            job_type=job_type,
            input_file_name=input_file_name,
            input_file_size=input_file_size,
            status=JobStatus.PENDING.value,
            progress=0,
        )

    def mark_processing(self, job_id: str, progress: int | None = None) -> ProcessingJob | None:
        job = self.get(job_id)
        if not job:
            return None
        return self.repository.update_lifecycle(
            job,
            status=JobStatus.PROCESSING.value,
            progress=progress,
            started_at=job.started_at or datetime.utcnow(),
        )

    def mark_completed(
        self,
        job_id: str,
        *,
        result_data: Mapping[str, Any] | None = None,
        output_file_url: str | None = None,
    ) -> ProcessingJob | None:
        job = self.get(job_id)
        if not job:
            return None
        return self.repository.update_lifecycle(
            job,
            status=JobStatus.COMPLETED.value,
            progress=100,
            result_data=result_data,
            output_file_url=output_file_url,
            completed_at=datetime.utcnow(),
        )

    def mark_failed(self, job_id: str, error_message: str) -> ProcessingJob | None:
        job = self.get(job_id)
        if not job:
            return None
        return self.repository.update_lifecycle(
            job,
            status=JobStatus.FAILED.value,
            error_message=error_message,
            completed_at=datetime.utcnow(),
        )

    def mark_cancelled(
        self,
        job_id: str,
        error_message: str = "Job cancelled by user",
    ) -> ProcessingJob | None:
        job = self.get(job_id)
        if not job or is_terminal_job_status(job.status):
            return job
        return self.repository.update_lifecycle(
            job,
            status=JobStatus.CANCELLED.value,
            error_message=error_message,
            completed_at=datetime.utcnow(),
        )


def build_pending_job_status(job_id: str, *, now: float | None = None) -> dict[str, Any]:
    timestamp = time.time() if now is None else now
    return {
        "job_id": job_id,
        "status": JobStatus.PENDING.value,
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def merge_celery_state_into_status(
    status_data: Mapping[str, Any],
    *,
    celery_state: object,
    celery_result: object = None,
    now: float | None = None,
) -> dict[str, Any]:
    """Return route-compatible status after overlaying Celery state.

    This is pure: callers decide whether and where to persist the merged status.
    Terminal Redis status wins because Celery result backend data may expire.
    """

    merged = dict(status_data)
    if is_terminal_job_status(merged.get("status")):
        return merged

    mapped = celery_state_to_job_status(celery_state)
    if mapped:
        merged["status"] = mapped
        merged["updated_at"] = time.time() if now is None else now

    if mapped == JobStatus.COMPLETED.value:
        merged["progress"] = 100
        merged["result"] = celery_result
    elif mapped == JobStatus.FAILED.value:
        merged["error"] = str(celery_result)

    return merged


def infer_job_type_from_status(status_data: Mapping[str, Any]) -> str:
    message = str(status_data.get("message") or "").lower()
    result = status_data.get("result") or {}
    result_keys = " ".join(str(key).lower() for key in result.keys()) if isinstance(result, Mapping) else ""
    haystack = f"{message} {result_keys}"

    for needle, job_type in JOB_TYPE_MESSAGE_PATTERNS:
        if needle in haystack:
            return job_type
    return "processing_job"


def redis_status_to_admin_job(
    status_data: Mapping[str, Any],
    *,
    fallback_job_id: str,
    sort_offset: float = 0,
) -> dict[str, Any]:
    created_at = datetime_from_epoch(status_data.get("created_at"))
    updated_at = datetime_from_epoch(status_data.get("updated_at")) or created_at
    result = status_data.get("result") or {}
    if not isinstance(result, Mapping):
        result = {}
    error = status_data.get("error")
    output_path = str(result.get("output_path") or "")
    input_file_name = (
        result.get("input_file_name")
        or output_path.rsplit("/", 1)[-1]
        or "Redis task"
    )

    return {
        "id": None,
        "job_id": status_data.get("job_id") or fallback_job_id,
        "user_id": None,
        "user_email": None,
        "job_type": infer_job_type_from_status(status_data),
        "status": status_data.get("status", "unknown"),
        "progress": int(
            status_data.get("progress")
            or (100 if normalize_job_status(status_data.get("status")) == JobStatus.COMPLETED.value else 0)
        ),
        "input_file_name": str(input_file_name),
        "input_file_size": int(result.get("file_size") or 0),
        "error_message": str(error) if error else None,
        "created_at": created_at or datetime.fromtimestamp(0),
        "started_at": None,
        "completed_at": (
            updated_at
            if normalize_job_status(status_data.get("status")) in (
                JobStatus.COMPLETED.value,
                JobStatus.FAILED.value,
            )
            else None
        ),
        "_sort": created_at.timestamp() if created_at else time.time() - sort_offset,
    }


def datetime_from_epoch(value: object) -> datetime | None:
    try:
        return datetime.fromtimestamp(float(value))
    except (TypeError, ValueError, OSError):
        return None
