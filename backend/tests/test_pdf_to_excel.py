import json
from unittest.mock import MagicMock

import pytest
from openpyxl import load_workbook
from reportlab.pdfgen import canvas


def _write_table_pdf(path):
    pdf = canvas.Canvas(str(path))
    lines = [
        "Item  Qty  Price",
        "Coffee  2  8.50",
        "Tea  1  4.00",
        "Total  3  12.50",
    ]
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


class TestPDFToExcelConversion:
    def test_converts_simple_text_table_to_xlsx(self, tmp_path):
        from app.domains.files.pdf_to_excel import convert_text_pdf_to_xlsx

        input_path = tmp_path / "table.pdf"
        output_path = tmp_path / "table.xlsx"
        _write_table_pdf(input_path)

        result = convert_text_pdf_to_xlsx(input_path=str(input_path), output_path=str(output_path))

        assert result["success"] is True
        assert output_path.exists()
        assert result["row_count"] >= 4

        workbook = load_workbook(output_path)
        sheet = workbook["Extracted text"]
        assert sheet["A1"].value == "Page"
        assert sheet["C2"].value == "Item"

    def test_rejects_scan_like_pdf(self, tmp_path):
        from app.domains.files.pdf_to_excel import PDFToExcelError, convert_text_pdf_to_xlsx

        input_path = tmp_path / "blank.pdf"
        output_path = tmp_path / "blank.xlsx"
        _write_blank_pdf(input_path)

        with pytest.raises(PDFToExcelError) as exc:
            convert_text_pdf_to_xlsx(input_path=str(input_path), output_path=str(output_path))

        assert "scanned or image-based PDF" in str(exc.value)
        assert not output_path.exists()


class TestPDFToExcelEndpoint:
    def _register_and_login(self, client, email: str) -> str:
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Excel User",
        })
        login = client.post("/api/v1/auth/login", data={
            "username": email,
            "password": "SecurePass123!",
        })
        return login.json()["access_token"]

    def test_pdf_to_excel_requires_login(self, client):
        response = client.post("/api/v1/files/pdf-to-excel", json={"file_id": "file_123"})

        assert response.status_code == 401

    def test_pdf_to_excel_creates_durable_user_job(self, monkeypatch, client, tmp_path):
        from app.core.database import get_db
        from app.models.user import ProcessingJob, User
        from app.services import file_service as file_service_module

        token = self._register_and_login(client, "excel-job@example.com")
        db = next(client.app.dependency_overrides[get_db]())
        try:
            user = db.query(User).filter(User.email == "excel-job@example.com").first()
        finally:
            db.close()

        input_path = tmp_path / "table.pdf"
        _write_table_pdf(input_path)
        saved_jobs = {}

        class FakeTask:
            def apply_async(self, args, task_id):
                saved_jobs["args"] = args
                saved_jobs["task_id"] = task_id
                return MagicMock(id=task_id)

        service = file_service_module.file_processing_service
        monkeypatch.setattr(service, "_generate_job_id", lambda: "job_excel_test")
        monkeypatch.setattr(
            service,
            "_get_file_metadata",
            lambda file_id: {
                "file_id": file_id,
                "filename": "table.pdf",
                "filepath": str(input_path),
                "size": input_path.stat().st_size,
            },
        )
        monkeypatch.setattr(
            service,
            "_save_job_status",
            lambda job_id, status_data: saved_jobs.setdefault("redis", (job_id, status_data)),
        )
        import app.tasks.excel_tasks as excel_tasks_module
        monkeypatch.setattr(excel_tasks_module, "pdf_to_excel_task", FakeTask())

        response = client.post(
            "/api/v1/files/pdf-to-excel",
            json={"file_id": "file_excel_test"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["job_id"] == "job_excel_test"
        assert saved_jobs["task_id"] == "job_excel_test"
        assert saved_jobs["args"][0] == str(input_path)
        assert saved_jobs["args"][1].endswith("table.xlsx")

        db = next(client.app.dependency_overrides[get_db]())
        try:
            job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_excel_test").first()
            assert job is not None
            assert job.user_id == user.id
            assert job.job_type == "pdf_to_excel"
            assert job.input_file_name == "table.pdf"
        finally:
            db.close()


class TestPDFToExcelTask:
    def test_task_updates_db_lifecycle_on_success(self, monkeypatch, tmp_path, client):
        from app.core.database import get_db
        from app.domains.jobs.repository import ProcessingJobRepository
        from app.domains.jobs.service import JobService
        from app.models.user import ProcessingJob
        import app.tasks.excel_tasks as excel_tasks_module

        output = tmp_path / "excel.xlsx"

        def fake_convert(**kwargs):
            output.write_bytes(b"xlsx")
            return {
                "success": True,
                "output_path": str(output),
                "file_size": output.stat().st_size,
            }

        db = next(client.app.dependency_overrides[get_db]())
        try:
            JobService(ProcessingJobRepository(db)).create_pending(
                job_id="job_excel_success",
                user_id=1,
                job_type="pdf_to_excel",
                input_file_name="input.pdf",
                input_file_size=100,
            )
            service = JobService(ProcessingJobRepository(db))
            monkeypatch.setattr(excel_tasks_module, "job_lifecycle", service)
            result = excel_tasks_module._run_pdf_to_excel_with_job_lifecycle(
                job_id="job_excel_success",
                operation=lambda: fake_convert(),
            )
            job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_excel_success").first()
            assert result["output_path"] == str(output)
            assert job.status == "completed"
            assert job.progress == 100
            assert json.loads(job.result_data)["output_path"] == str(output)
            assert job.output_file_url == str(output)
        finally:
            db.close()
