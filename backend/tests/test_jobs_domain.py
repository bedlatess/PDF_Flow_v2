"""Jobs domain boundary tests."""

from datetime import datetime

from app.domains.jobs.repository import ProcessingJobRepository
from app.domains.jobs.service import (
    JobService,
    build_pending_job_status,
    infer_job_type_from_status,
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

        unchanged = service.mark_cancelled("job_domain_lifecycle")
        assert unchanged is not None
        assert unchanged.status == "completed"
    finally:
        db.close()
