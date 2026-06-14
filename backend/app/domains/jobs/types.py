"""Shared job lifecycle types and pure status helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_JOB_STATUSES = {
    JobStatus.COMPLETED.value,
    JobStatus.FAILED.value,
    JobStatus.CANCELLED.value,
}

CELERY_STATE_TO_JOB_STATUS = {
    "PENDING": JobStatus.PENDING.value,
    "STARTED": JobStatus.PROCESSING.value,
    "RETRY": JobStatus.PROCESSING.value,
    "SUCCESS": JobStatus.COMPLETED.value,
    "FAILURE": JobStatus.FAILED.value,
    "REVOKED": JobStatus.CANCELLED.value,
}


@dataclass(frozen=True)
class JobArtifact:
    path: str
    name: str | None = None
    mime_type: str | None = None
    size: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"path": self.path}
        if self.name:
            payload["name"] = self.name
        if self.mime_type:
            payload["mime_type"] = self.mime_type
        if self.size is not None:
            payload["size"] = self.size
        return payload


@dataclass(frozen=True)
class JobResult:
    output_path: str | None = None
    output_files: tuple[str, ...] = ()
    text: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = dict(self.metadata)
        if self.output_path:
            payload["output_path"] = self.output_path
        if self.output_files:
            payload["output_files"] = list(self.output_files)
        if self.text is not None:
            payload["text"] = self.text
        return payload


@dataclass(frozen=True)
class JobError:
    message: str
    code: str | None = None

    def to_dict(self) -> dict[str, str]:
        payload = {"message": self.message}
        if self.code:
            payload["code"] = self.code
        return payload


@dataclass(frozen=True)
class JobProgress:
    value: int
    message: str | None = None

    def __post_init__(self) -> None:
        if self.value < 0 or self.value > 100:
            raise ValueError("Job progress must be between 0 and 100")

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"progress": self.value}
        if self.message:
            payload["message"] = self.message
        return payload


def normalize_job_status(value: object, default: JobStatus = JobStatus.PENDING) -> str:
    text = str(value or "").strip().lower()
    if text in {status.value for status in JobStatus}:
        return text
    return default.value


def is_terminal_job_status(value: object) -> bool:
    return normalize_job_status(value) in TERMINAL_JOB_STATUSES


def celery_state_to_job_status(value: object) -> str | None:
    return CELERY_STATE_TO_JOB_STATUS.get(str(value or "").strip().upper())
