import json
from unittest.mock import MagicMock

import pytest
from reportlab.pdfgen import canvas


def _write_text_pdf(path, lines=None):
    lines = lines or ["Quarterly Report", "This PDF contains selectable text.", "It should convert into a DOCX."]
    pdf = canvas.Canvas(str(path))
    y = 760
    for line in lines:
        pdf.drawString(72, y, line)
        y -= 24
    pdf.showPage()
    pdf.save()


def _write_blank_pdf(path):
    pdf = canvas.Canvas(str(path))
    pdf.showPage()
    pdf.save()


class TestPDFToWordConversion:
    def test_converts_text_pdf_to_docx(self, tmp_path):
        from app.domains.files.pdf_to_word import convert_text_pdf_to_docx

        input_path = tmp_path / "input.pdf"
        output_path = tmp_path / "output.docx"
        _write_text_pdf(input_path)

        result = convert_text_pdf_to_docx(
            input_path=str(input_path),
            output_path=str(output_path),
        )

        assert result["success"] is True
        assert result["output_path"] == str(output_path)
        assert output_path.exists()
        assert result["page_count"] == 1
        assert result["extracted_characters"] > 40

    def test_rejects_image_or_scan_like_pdf(self, tmp_path):
        from app.domains.files.pdf_to_word import PDFToWordError, convert_text_pdf_to_docx

        input_path = tmp_path / "blank.pdf"
        output_path = tmp_path / "blank.docx"
        _write_blank_pdf(input_path)

        with pytest.raises(PDFToWordError) as exc:
            convert_text_pdf_to_docx(
                input_path=str(input_path),
                output_path=str(output_path),
            )

        assert "scanned or image-based PDF" in str(exc.value)
        assert not output_path.exists()


class TestPDFToWordEndpoint:
    def _register_and_login(self, client, email: str) -> str:
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Word User",
        })
        login = client.post("/api/v1/auth/login", data={
            "username": email,
            "password": "SecurePass123!",
        })
        return login.json()["access_token"]

    def test_pdf_to_word_requires_login(self, client):
        response = client.post("/api/v1/files/pdf-to-word", json={"file_id": "file_123"})

        assert response.status_code == 401

    def test_pdf_to_word_creates_durable_user_job(self, monkeypatch, client, tmp_path):
        from app.core.database import get_db
        from app.models.user import ProcessingJob, User
        from app.services import file_service as file_service_module

        token = self._register_and_login(client, "word-job@example.com")
        db = next(client.app.dependency_overrides[get_db]())
        try:
            user = db.query(User).filter(User.email == "word-job@example.com").first()
        finally:
            db.close()

        input_path = tmp_path / "source.pdf"
        _write_text_pdf(input_path)
        saved_jobs = {}

        class FakeTask:
            def apply_async(self, args, task_id):
                saved_jobs["args"] = args
                saved_jobs["task_id"] = task_id
                return MagicMock(id=task_id)

        service = file_service_module.file_processing_service
        monkeypatch.setattr(service, "_generate_job_id", lambda: "job_word_test")
        monkeypatch.setattr(
            service,
            "_get_file_metadata",
            lambda file_id: {
                "file_id": file_id,
                "filename": "source.pdf",
                "filepath": str(input_path),
                "size": input_path.stat().st_size,
            },
        )
        monkeypatch.setattr(
            service,
            "_save_job_status",
            lambda job_id, status_data: saved_jobs.setdefault("redis", (job_id, status_data)),
        )
        import app.tasks.word_tasks as word_tasks_module
        monkeypatch.setattr(word_tasks_module, "pdf_to_word_task", FakeTask())

        response = client.post(
            "/api/v1/files/pdf-to-word",
            json={"file_id": "file_word_test"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["job_id"] == "job_word_test"
        assert saved_jobs["task_id"] == "job_word_test"
        assert saved_jobs["args"][0] == str(input_path)
        assert saved_jobs["args"][1].endswith("source.docx")

        db = next(client.app.dependency_overrides[get_db]())
        try:
            job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_word_test").first()
            assert job is not None
            assert job.user_id == user.id
            assert job.job_type == "pdf_to_word"
            assert job.input_file_name == "source.pdf"
        finally:
            db.close()


class TestPDFToWordTask:
    def test_task_updates_db_lifecycle_on_success(self, monkeypatch, tmp_path, client):
        from app.core.database import get_db
        from app.domains.jobs.repository import ProcessingJobRepository
        from app.domains.jobs.service import JobService
        from app.models.user import ProcessingJob
        import app.tasks.word_tasks as word_tasks_module

        output = tmp_path / "word.docx"

        def fake_convert(**kwargs):
            output.write_bytes(b"docx")
            return {
                "success": True,
                "output_path": str(output),
                "file_size": output.stat().st_size,
            }

        db = next(client.app.dependency_overrides[get_db]())
        try:
            JobService(ProcessingJobRepository(db)).create_pending(
                job_id="job_word_success",
                user_id=1,
                job_type="pdf_to_word",
                input_file_name="input.pdf",
                input_file_size=100,
            )
            service = JobService(ProcessingJobRepository(db))
            monkeypatch.setattr(word_tasks_module, "job_lifecycle", service)
            result = word_tasks_module._run_pdf_to_word_with_job_lifecycle(
                job_id="job_word_success",
                operation=lambda: fake_convert(),
            )
            job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_word_success").first()
            assert result["output_path"] == str(output)
            assert job.status == "completed"
            assert job.progress == 100
            assert json.loads(job.result_data)["output_path"] == str(output)
            assert job.output_file_url == str(output)
        finally:
            db.close()

    def test_task_marks_short_user_facing_failure(self, monkeypatch, client):
        from app.core.database import get_db
        from app.domains.files.pdf_to_word import PDFToWordError
        from app.domains.jobs.repository import ProcessingJobRepository
        from app.domains.jobs.service import JobService
        from app.models.user import ProcessingJob
        import app.tasks.word_tasks as word_tasks_module

        db = next(client.app.dependency_overrides[get_db]())
        try:
            JobService(ProcessingJobRepository(db)).create_pending(
                job_id="job_word_failure",
                user_id=1,
                job_type="pdf_to_word",
                input_file_name="scan.pdf",
                input_file_size=100,
            )
            service = JobService(ProcessingJobRepository(db))
            monkeypatch.setattr(word_tasks_module, "job_lifecycle", service)

            with pytest.raises(PDFToWordError):
                word_tasks_module._run_pdf_to_word_with_job_lifecycle(
                    job_id="job_word_failure",
                    operation=lambda: (_ for _ in ()).throw(PDFToWordError("This looks like a scanned PDF.")),
                )

            job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_word_failure").first()
            assert job.status == "failed"
            assert job.error_message == "This looks like a scanned PDF."
        finally:
            db.close()
