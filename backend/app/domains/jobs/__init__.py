"""Job lifecycle domain boundaries."""

from app.domains.jobs.repository import ProcessingJobRepository
from app.domains.jobs.service import (
    JobLifecycleWriter,
    JobService,
    JobStatusReader,
    build_pending_job_status,
    db_job_to_admin_job,
    db_job_to_route_status,
    infer_job_type_from_status,
    job_lifecycle,
    job_status_reader,
    merge_admin_jobs,
    merge_celery_state_into_status,
    redis_status_to_admin_job,
)
from app.domains.jobs.types import (
    JobArtifact,
    JobError,
    JobProgress,
    JobResult,
    JobStatus,
    celery_state_to_job_status,
    is_terminal_job_status,
    normalize_job_status,
)

__all__ = [
    "JobArtifact",
    "JobError",
    "JobProgress",
    "JobResult",
    "JobLifecycleWriter",
    "JobService",
    "JobStatusReader",
    "JobStatus",
    "ProcessingJobRepository",
    "build_pending_job_status",
    "celery_state_to_job_status",
    "db_job_to_admin_job",
    "db_job_to_route_status",
    "infer_job_type_from_status",
    "is_terminal_job_status",
    "job_lifecycle",
    "job_status_reader",
    "merge_admin_jobs",
    "merge_celery_state_into_status",
    "normalize_job_status",
    "redis_status_to_admin_job",
]
