"""PDF Celery task lifecycle tests."""

import json
from pathlib import Path

import pytest


def _write_minimal_pdf(path: Path) -> None:
    path.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
        b"0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer\n<< /Root 1 0 R /Size 4 >>\nstartxref\n190\n%%EOF\n"
    )


def test_compress_task_updates_durable_job_on_success(client, monkeypatch, tmp_path):
    from app.core.database import get_db
    from app.domains.jobs.repository import ProcessingJobRepository
    from app.domains.jobs.service import JobService
    from app.models.user import ProcessingJob
    from app.tasks import pdf_tasks

    input_path = tmp_path / "input.pdf"
    output_path = tmp_path / "compressed.pdf"
    _write_minimal_pdf(input_path)

    db = next(client.app.dependency_overrides[get_db]())
    try:
        JobService(ProcessingJobRepository(db)).create_pending(
            job_id="job_task_success",
            user_id=None,
            job_type="compress_pdf",
            input_file_name="input.pdf",
            input_file_size=input_path.stat().st_size,
        )
        service = JobService(ProcessingJobRepository(db))

        def mark_processing(job_id, progress=None):
            return service.mark_processing(job_id, progress=progress)

        def mark_completed(job_id, result_data=None, output_file_url=None):
            return service.mark_completed(
                job_id,
                result_data=result_data,
                output_file_url=output_file_url,
            )

        monkeypatch.setattr(pdf_tasks.job_lifecycle, "mark_processing", mark_processing)
        monkeypatch.setattr(pdf_tasks.job_lifecycle, "mark_completed", mark_completed)

        result = pdf_tasks._run_compress_pdf_with_job_lifecycle(
            job_id="job_task_success",
            file_path=str(input_path),
            output_path=str(output_path),
            quality="low",
        )

        db.expire_all()
        db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_task_success").first()
        assert db_job.status == "completed"
        assert db_job.progress == 100
        assert db_job.output_file_url == result["output_path"]
        stored_result = json.loads(db_job.result_data)
        assert stored_result["output_path"] == result["output_path"]
        assert result["success"] is True
    finally:
        db.close()


def test_compress_task_marks_durable_job_failed_before_retry(client, monkeypatch, tmp_path):
    from app.core.database import get_db
    from app.domains.jobs.repository import ProcessingJobRepository
    from app.domains.jobs.service import JobService
    from app.models.user import ProcessingJob
    from app.tasks import pdf_tasks

    input_path = tmp_path / "bad.pdf"
    input_path.write_bytes(b"not-a-pdf")
    output_path = tmp_path / "compressed.pdf"

    db = next(client.app.dependency_overrides[get_db]())
    try:
        JobService(ProcessingJobRepository(db)).create_pending(
            job_id="job_task_failure",
            user_id=None,
            job_type="compress_pdf",
            input_file_name="bad.pdf",
            input_file_size=input_path.stat().st_size,
        )
        service = JobService(ProcessingJobRepository(db))

        def mark_processing(job_id, progress=None):
            return service.mark_processing(job_id, progress=progress)

        def mark_failed(job_id, error_message):
            return service.mark_failed(job_id, error_message)

        monkeypatch.setattr(pdf_tasks.job_lifecycle, "mark_processing", mark_processing)
        monkeypatch.setattr(pdf_tasks.job_lifecycle, "mark_failed", mark_failed)

        def raise_original(exc):
            raise exc

        with pytest.raises(Exception):
            pdf_tasks._run_compress_pdf_with_job_lifecycle(
                job_id="job_task_failure",
                file_path=str(input_path),
                output_path=str(output_path),
                quality="low",
                retry=raise_original,
            )

        db.expire_all()
        db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_task_failure").first()
        assert db_job.status == "failed"
        assert db_job.error_message
        assert db_job.completed_at is not None
    finally:
        db.close()


def test_pdf_task_lifecycle_helper_updates_durable_job_for_output_files(client, monkeypatch):
    from app.core.database import get_db
    from app.domains.jobs.repository import ProcessingJobRepository
    from app.domains.jobs.service import JobService
    from app.models.user import ProcessingJob
    from app.tasks import pdf_tasks

    db = next(client.app.dependency_overrides[get_db]())
    try:
        JobService(ProcessingJobRepository(db)).create_pending(
            job_id="job_task_split_success",
            user_id=None,
            job_type="split_pdf",
            input_file_name="input.pdf",
            input_file_size=100,
        )
        service = JobService(ProcessingJobRepository(db))

        monkeypatch.setattr(
            pdf_tasks.job_lifecycle,
            "mark_processing",
            lambda job_id, progress=None: service.mark_processing(job_id, progress=progress),
        )
        monkeypatch.setattr(
            pdf_tasks.job_lifecycle,
            "mark_completed",
            lambda job_id, result_data=None, output_file_url=None: service.mark_completed(
                job_id,
                result_data=result_data,
                output_file_url=output_file_url,
            ),
        )

        result = pdf_tasks._run_pdf_task_with_job_lifecycle(
            job_id="job_task_split_success",
            operation_label="PDF split",
            operation=lambda: {
                "success": True,
                "output_files": ["/tmp/split_1.pdf", "/tmp/split_2.pdf"],
                "count": 2,
            },
        )

        db.expire_all()
        db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_task_split_success").first()
        assert db_job.status == "completed"
        assert db_job.progress == 100
        assert db_job.output_file_url == "/tmp/split_1.pdf"
        assert json.loads(db_job.result_data)["output_files"] == result["output_files"]
    finally:
        db.close()


def test_pdf_task_lifecycle_helper_marks_failure_before_retry(client, monkeypatch):
    from app.core.database import get_db
    from app.domains.jobs.repository import ProcessingJobRepository
    from app.domains.jobs.service import JobService
    from app.models.user import ProcessingJob
    from app.tasks import pdf_tasks

    db = next(client.app.dependency_overrides[get_db]())
    try:
        JobService(ProcessingJobRepository(db)).create_pending(
            job_id="job_task_rotate_failure",
            user_id=None,
            job_type="rotate_pdf",
            input_file_name="input.pdf",
            input_file_size=100,
        )
        service = JobService(ProcessingJobRepository(db))

        monkeypatch.setattr(
            pdf_tasks.job_lifecycle,
            "mark_processing",
            lambda job_id, progress=None: service.mark_processing(job_id, progress=progress),
        )
        monkeypatch.setattr(
            pdf_tasks.job_lifecycle,
            "mark_failed",
            lambda job_id, error_message: service.mark_failed(job_id, error_message),
        )

        def raise_original(exc):
            raise exc

        with pytest.raises(ValueError):
            pdf_tasks._run_pdf_task_with_job_lifecycle(
                job_id="job_task_rotate_failure",
                operation_label="PDF rotation",
                operation=lambda: (_ for _ in ()).throw(ValueError("rotation failed")),
                retry=raise_original,
            )

        db.expire_all()
        db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_task_rotate_failure").first()
        assert db_job.status == "failed"
        assert db_job.error_message == "rotation failed"
        assert db_job.completed_at is not None
    finally:
        db.close()
