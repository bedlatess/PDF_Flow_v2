"""Jobs domain boundary tests."""

from datetime import datetime

from app.domains.jobs.repository import ProcessingJobRepository
from app.domains.jobs.service import (
    JobService,
    build_pending_job_status,
    db_job_to_route_status,
    infer_job_type_from_status,
    merge_admin_jobs,
    merge_celery_state_into_status,
    redis_status_to_admin_job,
)
from app.domains.jobs.types import (
    JobStatus,
    celery_state_to_job_status,
    is_terminal_job_status,
    normalize_job_status,
)


def test_job_status_helpers_are_pure_and_route_compatible():
    original = {
        "job_id": "job_status",
        "status": "pending",
        "created_at": 100.0,
        "updated_at": 100.0,
    }

    merged = merge_celery_state_into_status(
        original,
        celery_state="SUCCESS",
        celery_result={"output_path": "/tmp/result.pdf"},
        now=125.0,
    )

    assert original["status"] == "pending"
    assert merged == {
        "job_id": "job_status",
        "status": "completed",
        "created_at": 100.0,
        "updated_at": 125.0,
        "progress": 100,
        "result": {"output_path": "/tmp/result.pdf"},
    }
    assert celery_state_to_job_status("STARTED") == JobStatus.PROCESSING.value
    assert celery_state_to_job_status("REVOKED") == JobStatus.CANCELLED.value
    assert normalize_job_status("unknown") == JobStatus.PENDING.value
    assert is_terminal_job_status("failed") is True


def test_terminal_redis_status_wins_over_expired_celery_result():
    original = {
        "job_id": "job_done",
        "status": "completed",
        "result": {"text": "done"},
    }

    merged = merge_celery_state_into_status(
        original,
        celery_state="PENDING",
        celery_result=None,
    )

    assert merged == original
    assert merged is not original


def test_successful_celery_result_can_carry_user_facing_failure():
    original = {
        "job_id": "job_scan",
        "status": "processing",
        "created_at": 100.0,
        "updated_at": 100.0,
    }

    merged = merge_celery_state_into_status(
        original,
        celery_state="SUCCESS",
        celery_result={"success": False, "error": "Use OCR PDF first."},
        now=140.0,
    )

    assert merged == {
        "job_id": "job_scan",
        "status": "failed",
        "created_at": 100.0,
        "updated_at": 140.0,
        "progress": 100,
        "error": "Use OCR PDF first.",
    }


def test_build_pending_job_status_keeps_existing_response_shape():
    status = build_pending_job_status("job_pending", now=200.5)

    assert status == {
        "job_id": "job_pending",
        "status": "pending",
        "created_at": 200.5,
        "updated_at": 200.5,
    }


def test_redis_status_to_admin_job_uses_shared_inference():
    status_data = {
        "job_id": "job_redis",
        "status": "completed",
        "progress": 100,
        "message": "PDF merge job queued",
        "created_at": 1780998441.0,
        "updated_at": 1780998442.0,
        "result": {
            "output_path": "/tmp/pdf-flow/uploads/merged.pdf",
            "file_size": 2048,
        },
    }

    admin_job = redis_status_to_admin_job(status_data, fallback_job_id="fallback")

    assert infer_job_type_from_status(status_data) == "merge_pdf"
    assert admin_job["job_id"] == "job_redis"
    assert admin_job["job_type"] == "merge_pdf"
    assert admin_job["status"] == "completed"
    assert admin_job["progress"] == 100
    assert admin_job["input_file_name"] == "merged.pdf"
    assert admin_job["input_file_size"] == 2048
    assert isinstance(admin_job["created_at"], datetime)
    assert admin_job["completed_at"] is not None
    assert admin_job["source"] == "redis"
    assert admin_job["sources"] == ["redis"]
    assert admin_job["is_durable"] is False


def test_merge_admin_jobs_prefers_db_and_marks_sources():
    created = datetime(2026, 1, 1, 12, 0, 0)
    db_job = {
        "id": 1,
        "job_id": "job_shared",
        "job_type": "compress_pdf",
        "status": "completed",
        "progress": 100,
        "created_at": created,
    }
    redis_job = {
        "id": None,
        "job_id": "job_shared",
        "job_type": "processing_job",
        "status": "pending",
        "progress": 0,
        "created_at": created,
    }
    redis_only = {
        "id": None,
        "job_id": "job_redis_only",
        "job_type": "ocr_pdf",
        "status": "processing",
        "progress": 50,
        "created_at": created,
    }

    merged = merge_admin_jobs([db_job], [redis_job, redis_only], limit=10)
    by_id = {job["job_id"]: job for job in merged}

    assert len([job for job in merged if job["job_id"] == "job_shared"]) == 1
    assert by_id["job_shared"]["id"] == 1
    assert by_id["job_shared"]["status"] == "completed"
    assert by_id["job_shared"]["source"] == "db"
    assert by_id["job_shared"]["sources"] == ["db", "redis"]
    assert by_id["job_shared"]["is_durable"] is True
    assert by_id["job_redis_only"]["source"] == "redis"
    assert by_id["job_redis_only"]["is_durable"] is False


def test_job_repository_and_service_lifecycle(client):
    from app.core.database import get_db
    from app.models.user import User

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = User(
            email="jobs-domain@example.com",
            hashed_password="hash",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        service = JobService(ProcessingJobRepository(db))
        created = service.create_pending(
            job_id="job_domain_lifecycle",
            user_id=user.id,
            job_type="merge_pdf",
            input_file_name="input.pdf",
            input_file_size=123,
        )

        assert created.status == "pending"
        assert created.progress == 0

        processing = service.mark_processing("job_domain_lifecycle", progress=35)
        assert processing is not None
        assert processing.status == "processing"
        assert processing.progress == 35
        assert processing.started_at is not None

        completed = service.mark_completed(
            "job_domain_lifecycle",
            result_data={"output_path": "/tmp/output.pdf"},
            output_file_url="/tmp/output.pdf",
        )
        assert completed is not None
        assert completed.status == "completed"
        assert completed.progress == 100
        assert completed.output_file_url == "/tmp/output.pdf"
        assert completed.completed_at is not None

        route_status = db_job_to_route_status(completed)
        assert route_status == {
            "job_id": "job_domain_lifecycle",
            "status": "completed",
            "created_at": completed.created_at.timestamp(),
            "updated_at": completed.completed_at.timestamp(),
            "progress": 100.0,
            "result": {"output_path": "/tmp/output.pdf"},
            "error": None,
        }

        unchanged = service.mark_cancelled("job_domain_lifecycle")
        assert unchanged is not None
        assert unchanged.status == "completed"
    finally:
        db.close()


def test_job_service_admin_jobs_merges_durable_and_redis(client):
    from app.core.database import get_db
    from app.models.user import ProcessingJob, User

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = User(
            email="jobs-admin-facade@example.com",
            hashed_password="hash",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        db.add(ProcessingJob(
            job_id="job_admin_facade_shared",
            user_id=user.id,
            job_type="compress_pdf",
            status="completed",
            progress=100,
            input_file_name="durable.pdf",
            input_file_size=100,
        ))
        db.commit()

        service = JobService(ProcessingJobRepository(db))
        jobs = service.admin_jobs(
            redis_jobs=[
                {
                    "job_id": "job_admin_facade_shared",
                    "status": "pending",
                    "job_type": "processing_job",
                    "created_at": datetime(2026, 1, 1),
                },
                {
                    "job_id": "job_admin_facade_redis",
                    "status": "processing",
                    "job_type": "ocr_pdf",
                    "created_at": datetime(2026, 1, 2),
                },
            ],
            limit=10,
        )

        by_id = {job["job_id"]: job for job in jobs}
        assert by_id["job_admin_facade_shared"]["source"] == "db"
        assert by_id["job_admin_facade_shared"]["sources"] == ["db", "redis"]
        assert by_id["job_admin_facade_shared"]["input_file_name"] == "durable.pdf"
        assert by_id["job_admin_facade_redis"]["source"] == "redis"
    finally:
        db.close()


def test_job_repository_allows_anonymous_processing_job(client):
    from app.core.database import get_db

    db = next(client.app.dependency_overrides[get_db]())
    try:
        service = JobService(ProcessingJobRepository(db))
        created = service.create_pending(
            job_id="job_domain_anonymous",
            user_id=None,
            job_type="compress_pdf",
            input_file_name="anonymous.pdf",
            input_file_size=321,
        )

        assert created.user_id is None
        assert created.job_type == "compress_pdf"
        assert created.status == "pending"
    finally:
        db.close()
