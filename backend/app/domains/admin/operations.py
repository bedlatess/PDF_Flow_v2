"""Admin operations, diagnostics, and maintenance domain."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.celery_worker import celery_app
from app.core.config import settings
from app.domains.admin.audit import write_admin_audit
from app.domains.admin.content import seed_defaults
from app.domains.admin.users import (
    is_test_account,
    serialize_admin_user,
    test_user_query,
)
from app.domains.jobs.service import datetime_from_epoch, redis_status_to_admin_job
from app.models.user import ApiErrorLog, FeedbackReport, ProcessingJob, User
from app.services.file_retention_service import file_retention_service
from app.services.file_service import file_processing_service


def list_redis_jobs(limit: int) -> list[dict]:
    jobs = []
    redis_client = file_processing_service.redis_client
    try:
        keys = list(redis_client.scan_iter("job:*", count=100))
    except AttributeError:
        keys = [
            key
            for key in getattr(redis_client, "store", {}).keys()
            if str(key).startswith("job:")
        ]
    except Exception:
        return jobs

    for index, key in enumerate(keys):
        try:
            raw = redis_client.get(key)
            if not raw:
                continue
            import json

            status_data = json.loads(raw)
        except Exception:
            continue

        jobs.append(redis_status_to_admin_job(
            status_data,
            fallback_job_id=str(key).replace("job:", ""),
            sort_offset=index,
        ))

    jobs.sort(key=lambda item: item["_sort"], reverse=True)
    for item in jobs:
        item.pop("_sort", None)
    return jobs[:limit]


def check_services(db: Session) -> dict:
    services = {}
    try:
        db.execute(text("SELECT 1"))
        services["database"] = {"status": "healthy", "detail": "Postgres reachable"}
    except Exception as exc:
        services["database"] = {"status": "unhealthy", "detail": str(exc)}

    try:
        file_processing_service.redis_client.ping()
        services["redis"] = {"status": "healthy", "detail": "Redis reachable"}
    except Exception as exc:
        services["redis"] = {"status": "unhealthy", "detail": str(exc)}

    if services.get("redis", {}).get("status") != "healthy":
        services["celery_worker"] = {
            "status": "unhealthy",
            "detail": "Redis broker is unavailable.",
        }
    else:
        try:
            responses = celery_app.control.ping(timeout=1.0)
            services["celery_worker"] = {
                "status": "healthy" if responses else "degraded",
                "detail": (
                    f"{len(responses)} worker response(s)"
                    if responses
                    else "No worker responded to Celery ping."
                ),
            }
        except Exception as exc:
            services["celery_worker"] = {
                "status": "degraded",
                "detail": f"Celery ping failed: {exc}",
            }
    return services


def current_migration_version(db: Session) -> str | None:
    try:
        row = db.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).first()
        return row[0] if row else None
    except Exception:
        return None


def list_all_jobs(
    db: Session,
    *,
    limit: int,
    status_filter: str | None = None,
) -> list[dict]:
    safe_limit = min(max(limit, 1), 100)
    redis_jobs = list_redis_jobs(safe_limit)
    if status_filter:
        redis_jobs = [job for job in redis_jobs if job["status"] == status_filter]

    query = (
        db.query(ProcessingJob, User.email)
        .outerjoin(User, ProcessingJob.user_id == User.id)
        .order_by(ProcessingJob.created_at.desc())
    )
    if status_filter:
        query = query.filter(ProcessingJob.status == status_filter)

    rows = query.limit(safe_limit).all()
    db_jobs = [
        {
            "id": job.id,
            "job_id": job.job_id,
            "user_id": job.user_id,
            "user_email": email,
            "job_type": job.job_type,
            "status": job.status,
            "progress": job.progress,
            "input_file_name": job.input_file_name,
            "input_file_size": job.input_file_size,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }
        for job, email in rows
    ]
    seen = {job["job_id"] for job in redis_jobs}
    merged = redis_jobs + [job for job in db_jobs if job["job_id"] not in seen]
    merged.sort(key=lambda item: item["created_at"], reverse=True)
    return merged[:safe_limit]


def safe_diag(value: object | None, fallback: str = "none", max_length: int = 240) -> str:
    if value is None:
        return fallback
    text_value = str(value).replace("\r", " ").replace("\n", " ").strip()
    if not text_value:
        return fallback
    return text_value if len(text_value) <= max_length else f"{text_value[:max_length - 3]}..."


def safe_url_for_diagnostics(value: object | None, max_length: int = 180) -> str:
    text_value = safe_diag(value, max_length=max_length)
    if text_value == "none":
        return text_value
    try:
        parts = urlsplit(text_value)
        if parts.scheme and parts.netloc:
            text_value = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        elif parts.path:
            text_value = parts.path
    except ValueError:
        pass
    return safe_diag(text_value, max_length=max_length)


def build_diagnostic_summary(
    *,
    generated_at: datetime,
    services: dict,
    errors: list[ApiErrorLog],
    failed_jobs: list[dict],
    feedback: list[FeedbackReport],
    open_feedback_count: int,
    failed_jobs_count: int,
    api_error_count: int,
) -> str:
    service_status = ", ".join(
        f"{name}={getattr(status, 'status', None) or status.get('status', 'unknown')}"
        for name, status in services.items()
    ) or "none"

    lines = [
        "PDF-Flow diagnostic packet",
        f"Generated: {generated_at.isoformat()}Z",
        f"Environment: {settings.ENVIRONMENT}",
        f"Version: {settings.VERSION}",
        f"Services: {service_status}",
        f"Counts: api_errors={api_error_count}, failed_jobs={failed_jobs_count}, open_feedback={open_feedback_count}",
    ]

    if errors:
        error = errors[0]
        lines.extend([
            "",
            "Latest API error:",
            f"- request_id={safe_diag(error.request_id)}",
            f"- route={error.method} {safe_diag(error.path, max_length=180)}",
            f"- status={error.status_code}, type={safe_diag(error.error_type)}",
            f"- message={safe_diag(error.error_message or error.traceback_summary, max_length=280)}",
        ])

    if failed_jobs:
        job = failed_jobs[0]
        lines.extend([
            "",
            "Latest failed job:",
            f"- job_id={safe_diag(job.get('job_id'))}",
            f"- type={safe_diag(job.get('job_type'))}, status={safe_diag(job.get('status'))}, progress={job.get('progress', 0)}",
            f"- file={safe_diag(job.get('input_file_name'), max_length=180)}, size={job.get('input_file_size', 0)}",
            f"- error={safe_diag(job.get('error_message'), max_length=280)}",
        ])

    if feedback:
        item = feedback[0]
        lines.extend([
            "",
            "Latest open feedback:",
            f"- id={item.id}, status={safe_diag(item.status)}, severity={safe_diag(item.severity)}",
            f"- title={safe_diag(item.title, max_length=180)}",
            f"- page={safe_url_for_diagnostics(item.page_url)}",
            f"- diagnostic_code={safe_diag(item.diagnostic_code)}",
        ])

    lines.extend([
        "",
        "Privacy note: request bodies and document contents are not included in this packet.",
    ])
    return "\n".join(lines)


def get_operations_overview(db: Session) -> dict:
    seed_defaults(db)
    users = db.query(User).order_by(User.created_at.desc()).limit(8).all()
    all_users = db.query(User).all()
    jobs = list_all_jobs(db, limit=50)
    failed_jobs = [job for job in jobs if job["status"] == "failed"]
    running_jobs = [job for job in jobs if job["status"] in ("pending", "processing")]

    return {
        "generated_at": datetime.utcnow(),
        "services": check_services(db),
        "total_users": len(all_users),
        "active_users": len([user for user in all_users if user.is_active]),
        "banned_users": len([user for user in all_users if not user.is_active]),
        "test_users": len([user for user in all_users if is_test_account(user)]),
        "total_jobs": db.query(ProcessingJob).count(),
        "visible_jobs": len(jobs),
        "failed_jobs": len(failed_jobs),
        "running_jobs": len(running_jobs),
        "recent_users": [serialize_admin_user(user) for user in users],
        "recent_failed_jobs": failed_jobs[:5],
        "recent_jobs": jobs[:8],
    }


def get_health_report(db: Session) -> dict:
    seed_defaults(db)
    jobs = list_all_jobs(db, limit=50)
    failed_jobs = [job for job in jobs if job["status"] == "failed"]
    running_jobs = [job for job in jobs if job["status"] in ("pending", "processing")]
    recent_error = db.query(ApiErrorLog).order_by(ApiErrorLog.created_at.desc()).first()
    recent_feedback = (
        db.query(FeedbackReport)
        .filter(FeedbackReport.status.in_(["new", "reviewing"]))
        .order_by(FeedbackReport.created_at.desc())
        .first()
    )

    return {
        "generated_at": datetime.utcnow(),
        "app_version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "migration_version": current_migration_version(db),
        "services": check_services(db),
        "users_count": db.query(User).count(),
        "active_users_count": db.query(User).filter(User.is_active == True).count(),  # noqa: E712
        "open_feedback_count": db.query(FeedbackReport).filter(
            FeedbackReport.status.in_(["new", "reviewing"])
        ).count(),
        "api_error_count": db.query(ApiErrorLog).count(),
        "failed_jobs_count": len(failed_jobs),
        "running_jobs_count": len(running_jobs),
        "recent_error_path": recent_error.path if recent_error else None,
        "recent_feedback_title": recent_feedback.title if recent_feedback else None,
    }


def list_jobs(
    db: Session,
    *,
    status_filter: str | None = None,
    limit: int = 50,
) -> list[dict]:
    return list_all_jobs(db, limit=limit, status_filter=status_filter)


def list_api_errors(db: Session, *, limit: int = 50) -> list[ApiErrorLog]:
    safe_limit = min(max(limit, 1), 100)
    return (
        db.query(ApiErrorLog)
        .order_by(ApiErrorLog.created_at.desc())
        .limit(safe_limit)
        .all()
    )


def get_diagnostics(db: Session) -> dict:
    generated_at = datetime.utcnow()
    errors = list_api_errors(db, limit=20)
    jobs = list_all_jobs(db, limit=50)
    failed_jobs = [job for job in jobs if job["status"] == "failed"][:10]
    failed_jobs_count = len([job for job in jobs if job["status"] == "failed"])
    feedback = (
        db.query(FeedbackReport)
        .filter(FeedbackReport.status.in_(["new", "reviewing"]))
        .order_by(FeedbackReport.created_at.desc())
        .limit(10)
        .all()
    )
    open_feedback_count = db.query(FeedbackReport).filter(
        FeedbackReport.status.in_(["new", "reviewing"])
    ).count()
    api_error_count = db.query(ApiErrorLog).count()
    services = check_services(db)

    return {
        "generated_at": generated_at,
        "recent_errors": errors,
        "recent_failed_jobs": failed_jobs,
        "recent_feedback": [
            {
                "id": item.id,
                "title": item.title,
                "status": item.status,
                "severity": item.severity,
                "page_url": item.page_url,
                "diagnostic_code": item.diagnostic_code,
                "created_at": item.created_at,
            }
            for item in feedback
        ],
        "diagnostic_summary": build_diagnostic_summary(
            generated_at=generated_at,
            services=services,
            errors=errors,
            failed_jobs=failed_jobs,
            feedback=feedback,
            open_feedback_count=open_feedback_count,
            failed_jobs_count=failed_jobs_count,
            api_error_count=api_error_count,
        ),
        "open_feedback_count": open_feedback_count,
        "failed_jobs_count": failed_jobs_count,
        "api_error_count": api_error_count,
    }


def get_maintenance_summary(db: Session, *, admin: User) -> dict:
    jobs = list_all_jobs(db, limit=50)
    return {
        "test_users_count": test_user_query(db, admin).count(),
        "live_acceptance_feedback_count": db.query(FeedbackReport).filter(
            FeedbackReport.status.in_(["new", "reviewing"]),
            FeedbackReport.title.ilike("live acceptance%"),
        ).count(),
        "open_feedback_count": db.query(FeedbackReport).filter(
            FeedbackReport.status.in_(["new", "reviewing"])
        ).count(),
        "api_error_count": db.query(ApiErrorLog).count(),
        "failed_jobs_count": len([job for job in jobs if job["status"] == "failed"]),
        "running_jobs_count": len(
            [job for job in jobs if job["status"] in ("pending", "processing")]
        ),
        "file_retention": file_retention_service.preview(),
    }


def cleanup_expired_files(db: Session, *, request: Request, admin: User) -> dict:
    result = file_retention_service.cleanup()
    write_admin_audit(
        db,
        request,
        admin,
        "cleanup",
        "file_retention",
        settings.UPLOAD_DIR,
        detail=f"removed={result['removed_count']}, bytes={result['removed_bytes']}",
    )
    db.commit()
    return result
