"""Repository for durable processing job records."""

from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Mapping

from sqlalchemy.orm import Session

from app.domains.jobs.types import JobStatus, normalize_job_status
from app.models.user import ProcessingJob


class ProcessingJobRepository:
    """Small persistence boundary around the existing ProcessingJob model."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_job_id(self, job_id: str) -> ProcessingJob | None:
        return self.db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()

    def create(
        self,
        *,
        job_id: str,
        user_id: int,
        job_type: str,
        input_file_name: str,
        input_file_size: int,
        status: str = JobStatus.PENDING.value,
        progress: int = 0,
        result_data: Mapping[str, Any] | None = None,
        output_file_url: str | None = None,
        error_message: str | None = None,
    ) -> ProcessingJob:
        job = ProcessingJob(
            job_id=job_id,
            user_id=user_id,
            job_type=job_type,
            status=normalize_job_status(status),
            progress=progress,
            input_file_name=input_file_name,
            input_file_size=input_file_size,
            output_file_url=output_file_url,
            result_data=_dump_json(result_data),
            error_message=error_message,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_lifecycle(
        self,
        job: ProcessingJob,
        *,
        status: str | None = None,
        progress: int | None = None,
        result_data: Mapping[str, Any] | None = None,
        output_file_url: str | None = None,
        error_message: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> ProcessingJob:
        if status is not None:
            job.status = normalize_job_status(status)
        if progress is not None:
            job.progress = max(0, min(100, int(progress)))
        if result_data is not None:
            job.result_data = _dump_json(result_data)
        if output_file_url is not None:
            job.output_file_url = output_file_url
        if error_message is not None:
            job.error_message = error_message
        if started_at is not None:
            job.started_at = started_at
        if completed_at is not None:
            job.completed_at = completed_at

        self.db.commit()
        self.db.refresh(job)
        return job


def _dump_json(value: Mapping[str, Any] | None) -> str | None:
    if value is None:
        return None
    return json.dumps(dict(value), ensure_ascii=False, sort_keys=True)
