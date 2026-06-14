"""OCR and Office durable job lifecycle tests."""

import json

import pytest


def test_ocr_lifecycle_helper_updates_durable_job_on_success(client, monkeypatch):
    from app.core.database import get_db
    from app.domains.jobs.repository import ProcessingJobRepository
    from app.domains.jobs.service import JobService
    from app.models.user import ProcessingJob
    from app.tasks import ocr_tasks

    db = next(client.app.dependency_overrides[get_db]())
    try:
        JobService(ProcessingJobRepository(db)).create_pending(
            job_id="job_ocr_success",
            user_id=None,
            job_type="ocr_pdf",
            input_file_name="input.pdf",
            input_file_size=100,
        )
        service = JobService(ProcessingJobRepository(db))
        monkeypatch.setattr(
            ocr_tasks.job_lifecycle,
            "mark_processing",
            lambda job_id, progress=None: service.mark_processing(job_id, progress=progress),
        )
        monkeypatch.setattr(
            ocr_tasks.job_lifecycle,
            "mark_completed",
            lambda job_id, result_data=None, output_file_url=None: service.mark_completed(
                job_id,
                result_data=result_data,
                output_file_url=output_file_url,
            ),
        )

        result = ocr_tasks._run_ocr_task_with_job_lifecycle(
            job_id="job_ocr_success",
            operation_label="OCR extraction",
            operation=lambda: {
                "success": True,
                "text": "hello",
                "page_count": 1,
                "average_confidence": 98,
            },
        )

        db.expire_all()
        db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_ocr_success").first()
        assert db_job.status == "completed"
        assert db_job.progress == 100
        assert db_job.output_file_url is None
        assert json.loads(db_job.result_data)["text"] == result["text"]
    finally:
        db.close()


def test_ocr_lifecycle_helper_marks_failed_before_retry(client, monkeypatch):
    from app.core.database import get_db
    from app.domains.jobs.repository import ProcessingJobRepository
    from app.domains.jobs.service import JobService
    from app.models.user import ProcessingJob
    from app.tasks import ocr_tasks

    db = next(client.app.dependency_overrides[get_db]())
    try:
        JobService(ProcessingJobRepository(db)).create_pending(
            job_id="job_ocr_failure",
            user_id=None,
            job_type="ocr_pdf",
            input_file_name="input.pdf",
            input_file_size=100,
        )
        service = JobService(ProcessingJobRepository(db))
        monkeypatch.setattr(
            ocr_tasks.job_lifecycle,
            "mark_processing",
            lambda job_id, progress=None: service.mark_processing(job_id, progress=progress),
        )
        monkeypatch.setattr(
            ocr_tasks.job_lifecycle,
            "mark_failed",
            lambda job_id, error_message: service.mark_failed(job_id, error_message),
        )

        def raise_original(exc):
            raise exc

        with pytest.raises(RuntimeError):
            ocr_tasks._run_ocr_task_with_job_lifecycle(
                job_id="job_ocr_failure",
                operation_label="OCR extraction",
                operation=lambda: (_ for _ in ()).throw(RuntimeError("ocr failed")),
                retry=raise_original,
            )

        db.expire_all()
        db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_ocr_failure").first()
        assert db_job.status == "failed"
        assert db_job.error_message == "ocr failed"
        assert db_job.completed_at is not None
    finally:
        db.close()


def test_office_lifecycle_helper_updates_durable_job_on_success(client, monkeypatch):
    from app.core.database import get_db
    from app.domains.jobs.repository import ProcessingJobRepository
    from app.domains.jobs.service import JobService
    from app.models.user import ProcessingJob
    from app.tasks import office_tasks

    db = next(client.app.dependency_overrides[get_db]())
    try:
        JobService(ProcessingJobRepository(db)).create_pending(
            job_id="job_office_success",
            user_id=None,
            job_type="office_to_pdf",
            input_file_name="input.docx",
            input_file_size=100,
        )
        service = JobService(ProcessingJobRepository(db))
        monkeypatch.setattr(
            office_tasks.job_lifecycle,
            "mark_processing",
            lambda job_id, progress=None: service.mark_processing(job_id, progress=progress),
        )
        monkeypatch.setattr(
            office_tasks.job_lifecycle,
            "mark_completed",
            lambda job_id, result_data=None, output_file_url=None: service.mark_completed(
                job_id,
                result_data=result_data,
                output_file_url=output_file_url,
            ),
        )

        result = office_tasks._run_office_task_with_job_lifecycle(
            job_id="job_office_success",
            operation_label="Office to PDF conversion",
            operation=lambda: {
                "success": True,
                "output_path": "/tmp/output.pdf",
                "file_size": 123,
                "error": None,
            },
        )

        db.expire_all()
        db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_office_success").first()
        assert db_job.status == "completed"
        assert db_job.progress == 100
        assert db_job.output_file_url == result["output_path"]
        assert json.loads(db_job.result_data)["output_path"] == result["output_path"]
    finally:
        db.close()


def test_office_lifecycle_helper_marks_failed_for_false_result(client, monkeypatch):
    from app.core.database import get_db
    from app.domains.jobs.repository import ProcessingJobRepository
    from app.domains.jobs.service import JobService
    from app.models.user import ProcessingJob
    from app.tasks import office_tasks

    db = next(client.app.dependency_overrides[get_db]())
    try:
        JobService(ProcessingJobRepository(db)).create_pending(
            job_id="job_office_failure",
            user_id=None,
            job_type="office_to_pdf",
            input_file_name="input.docx",
            input_file_size=100,
        )
        service = JobService(ProcessingJobRepository(db))
        monkeypatch.setattr(
            office_tasks.job_lifecycle,
            "mark_processing",
            lambda job_id, progress=None: service.mark_processing(job_id, progress=progress),
        )
        monkeypatch.setattr(
            office_tasks.job_lifecycle,
            "mark_failed",
            lambda job_id, error_message: service.mark_failed(job_id, error_message),
        )

        result = office_tasks._run_office_task_with_job_lifecycle(
            job_id="job_office_failure",
            operation_label="Office to PDF conversion",
            operation=lambda: {
                "success": False,
                "output_path": None,
                "file_size": 0,
                "error": "libreoffice failed",
            },
        )

        db.expire_all()
        db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_office_failure").first()
        assert result["success"] is False
        assert db_job.status == "failed"
        assert db_job.error_message == "libreoffice failed"
        assert db_job.completed_at is not None
    finally:
        db.close()
