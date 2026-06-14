"""Job lifecycle service and route/admin job helpers."""

from __future__ import annotations

from datetime import datetime
import json
import logging
import time
from typing import Any, Mapping

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.domains.jobs.repository import ProcessingJobRepository
from app.domains.jobs.types import (
    JobStatus,
    celery_state_to_job_status,
    is_terminal_job_status,
    normalize_job_status,
)
from app.models.user import ProcessingJob


logger = logging.getLogger(__name__)


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

    def route_status_for_job_id(self, job_id: str) -> dict[str, Any] | None:
        job = self.get(job_id)
        if not job:
            return None
        return db_job_to_route_status(job)

    def admin_jobs(
        self,
        *,
        redis_jobs: list[dict[str, Any]],
        limit: int,
        status_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        db_jobs = [
            db_job_to_admin_job(job, user_email=email)
            for job, email in self.repository.list_recent_with_user_email(
                limit=limit,
                status_filter=status_filter,
            )
        ]
        return merge_admin_jobs(db_jobs, redis_jobs, limit=limit)

    def create_pending(
        self,
        *,
        job_id: str,
        user_id: int | None,
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


class JobLifecycleWriter:
    """Best-effort durable lifecycle writer used by file services and tasks."""

    def create_pending(
        self,
        *,
        job_id: str,
        user_id: int | None,
        job_type: str,
        input_file_name: str,
        input_file_size: int,
        db: Session | None = None,
    ) -> ProcessingJob | None:
        return _with_optional_session(
            db,
            lambda session: JobService(ProcessingJobRepository(session)).create_pending(
                job_id=job_id,
                user_id=user_id,
                job_type=job_type,
                input_file_name=input_file_name,
                input_file_size=input_file_size,
            ),
            "create processing job",
            job_id,
        )

    def mark_processing(self, job_id: str, *, progress: int | None = None) -> ProcessingJob | None:
        return _with_optional_session(
            None,
            lambda session: JobService(ProcessingJobRepository(session)).mark_processing(
                job_id,
                progress=progress,
            ),
            "mark processing job processing",
            job_id,
        )

    def mark_completed(
        self,
        job_id: str,
        *,
        result_data: Mapping[str, Any] | None = None,
        output_file_url: str | None = None,
    ) -> ProcessingJob | None:
        return _with_optional_session(
            None,
            lambda session: JobService(ProcessingJobRepository(session)).mark_completed(
                job_id,
                result_data=result_data,
                output_file_url=output_file_url,
            ),
            "mark processing job completed",
            job_id,
        )

    def mark_failed(self, job_id: str, *, error_message: str) -> ProcessingJob | None:
        return _with_optional_session(
            None,
            lambda session: JobService(ProcessingJobRepository(session)).mark_failed(
                job_id,
                error_message,
            ),
            "mark processing job failed",
            job_id,
        )


job_lifecycle = JobLifecycleWriter()


class JobStatusReader:
    """Best-effort durable status reader used behind Redis-first routes."""

    def route_status(
        self,
        job_id: str,
        *,
        session_factory=None,
    ) -> dict[str, Any] | None:
        factory = session_factory or SessionLocal
        try:
            session = factory()
            try:
                return JobService(ProcessingJobRepository(session)).route_status_for_job_id(job_id)
            finally:
                session.close()
        except Exception as exc:
            logger.warning("Durable job status fallback failed for %s: %s", job_id, exc)
            return None


job_status_reader = JobStatusReader()


def build_pending_job_status(job_id: str, *, now: float | None = None) -> dict[str, Any]:
    timestamp = time.time() if now is None else now
    return {
        "job_id": job_id,
        "status": JobStatus.PENDING.value,
        "created_at": timestamp,
        "updated_at": timestamp,
    }

def _with_optional_session(
    db: Session | None,
    operation,
    label: str,
    job_id: str,
) -> ProcessingJob | None:
    owns_session = db is None
    session = db or SessionLocal()
    try:
        return operation(session)
    except Exception as exc:
        try:
            session.rollback()
        except Exception:
            pass
        logger.warning("%s failed for %s: %s", label, job_id, exc)
        return None
    finally:
        if owns_session:
            session.close()


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
        "output_file_url": output_path or None,
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
        "source": "redis",
        "sources": ["redis"],
        "is_durable": False,
        "_sort": created_at.timestamp() if created_at else time.time() - sort_offset,
    }


def db_job_to_admin_job(job: ProcessingJob, *, user_email: str | None = None) -> dict[str, Any]:
    return {
        "id": job.id,
        "job_id": job.job_id,
        "user_id": job.user_id,
        "user_email": user_email,
        "job_type": job.job_type,
        "status": normalize_job_status(job.status),
        "progress": int(job.progress or 0),
        "input_file_name": job.input_file_name,
        "input_file_size": int(job.input_file_size or 0),
        "output_file_url": job.output_file_url,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "source": "db",
        "sources": ["db"],
        "is_durable": True,
    }


def merge_admin_jobs(
    db_jobs: list[dict[str, Any]],
    redis_jobs: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    """Merge DB durable and Redis active jobs for admin views.

    DB durable rows win for duplicate job IDs. Redis-only rows remain visible so
    legacy and rollback-path tasks do not disappear from the operations view.
    """

    merged_by_id: dict[str, dict[str, Any]] = {}

    for job in db_jobs:
        job_id = str(job.get("job_id") or "")
        if not job_id:
            continue
        normalized = dict(job)
        normalized["source"] = "db"
        normalized["sources"] = ["db"]
        normalized["is_durable"] = True
        merged_by_id[job_id] = normalized

    for job in redis_jobs:
        job_id = str(job.get("job_id") or "")
        if not job_id:
            continue
        if job_id in merged_by_id:
            sources = list(merged_by_id[job_id].get("sources") or ["db"])
            if "redis" not in sources:
                sources.append("redis")
            merged_by_id[job_id]["sources"] = sources
            continue
        normalized = dict(job)
        normalized["source"] = "redis"
        normalized["sources"] = ["redis"]
        normalized["is_durable"] = False
        merged_by_id[job_id] = normalized

    merged = list(merged_by_id.values())
    merged.sort(key=lambda item: item.get("created_at") or datetime.fromtimestamp(0), reverse=True)
    return merged[:limit]


def db_job_to_route_status(job: ProcessingJob) -> dict[str, Any]:
    """Serialize a durable DB job into the existing /files/jobs response shape."""

    result = _load_json_mapping(job.result_data)
    status = normalize_job_status(job.status)
    return {
        "job_id": job.job_id,
        "status": status,
        "created_at": job.created_at.timestamp() if job.created_at else time.time(),
        "updated_at": _job_updated_at(job).timestamp(),
        "progress": float(job.progress or 0),
        "result": result if result else None,
        "error": job.error_message,
    }


def _job_updated_at(job: ProcessingJob) -> datetime:
    if job.completed_at:
        return job.completed_at
    if job.started_at:
        return job.started_at
    return job.created_at or datetime.utcnow()


def _load_json_mapping(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def datetime_from_epoch(value: object) -> datetime | None:
    try:
        return datetime.fromtimestamp(float(value))
    except (TypeError, ValueError, OSError):
        return None
