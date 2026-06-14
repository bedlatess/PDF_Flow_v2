import asyncio
import json
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException


class TestHTMLToPDFValidation:
    def test_rejects_localhost_url(self):
        from app.domains.files.html_to_pdf import validate_url_for_html_to_pdf

        with pytest.raises(HTTPException) as exc:
            validate_url_for_html_to_pdf("http://localhost:8000/private")

        assert exc.value.status_code == 400

    def test_rejects_private_ip_url(self):
        from app.domains.files.html_to_pdf import validate_url_for_html_to_pdf

        with pytest.raises(HTTPException) as exc:
            validate_url_for_html_to_pdf("http://127.0.0.1/internal")

        assert exc.value.status_code == 400

    def test_rejects_url_credentials(self):
        from app.domains.files.html_to_pdf import validate_url_for_html_to_pdf

        with pytest.raises(HTTPException) as exc:
            validate_url_for_html_to_pdf("https://user:pass@example.com/report")

        assert exc.value.status_code == 400

    def test_rejects_large_html_text(self):
        from app.domains.files.html_to_pdf import validate_html_text

        with pytest.raises(HTTPException) as exc:
            validate_html_text("x" * (513 * 1024))

        assert exc.value.status_code == 413

    def test_render_request_guard_aborts_private_url(self):
        from app.domains.files.html_to_pdf import _guard_render_request

        events = []

        class Request:
            url = "http://127.0.0.1:8000/private.png"

        class Route:
            request = Request()

            def abort(self):
                events.append("abort")

            def continue_(self):
                events.append("continue")

        _guard_render_request(Route())

        assert events == ["abort"]

    def test_render_request_guard_allows_data_url(self):
        from app.domains.files.html_to_pdf import _guard_render_request

        events = []

        class Request:
            url = "data:image/png;base64,AA=="

        class Route:
            request = Request()

            def abort(self):
                events.append("abort")

            def continue_(self):
                events.append("continue")

        _guard_render_request(Route())

        assert events == ["continue"]


class TestHTMLToPDFEndpoint:
    def _register_and_login(self, client, email: str) -> str:
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "HTML User",
        })
        login = client.post("/api/v1/auth/login", data={
            "username": email,
            "password": "SecurePass123!",
        })
        return login.json()["access_token"]

    def test_html_to_pdf_requires_login(self, client):
        response = client.post("/api/v1/files/html-to-pdf", json={
            "mode": "html",
            "html": "<h1>Hello</h1>",
        })

        assert response.status_code == 401

    def test_html_to_pdf_rejects_private_url_before_queue(self, client):
        token = self._register_and_login(client, "html-private@example.com")

        response = client.post(
            "/api/v1/files/html-to-pdf",
            json={"mode": "url", "url": "http://127.0.0.1:8000/secret"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400

    def test_html_to_pdf_creates_durable_user_job(self, monkeypatch, client):
        from app.core.database import get_db
        from app.models.user import ProcessingJob, User
        from app.services import file_service as file_service_module

        token = self._register_and_login(client, "html-job@example.com")
        db = next(client.app.dependency_overrides[get_db]())
        try:
            user = db.query(User).filter(User.email == "html-job@example.com").first()
        finally:
            db.close()

        saved_jobs = {}

        class FakeTask:
            def apply_async(self, args, task_id):
                saved_jobs["args"] = args
                saved_jobs["task_id"] = task_id
                return MagicMock(id=task_id)

        monkeypatch.setattr(file_service_module.file_processing_service, "_generate_job_id", lambda: "job_html_test")
        monkeypatch.setattr(
            file_service_module.file_processing_service,
            "_save_job_status",
            lambda job_id, status_data: saved_jobs.setdefault("redis", (job_id, status_data)),
        )
        monkeypatch.setattr(file_service_module, "html_to_pdf_task", FakeTask(), raising=False)
        import app.tasks.html_tasks as html_tasks_module
        monkeypatch.setattr(html_tasks_module, "html_to_pdf_task", FakeTask())

        response = client.post(
            "/api/v1/files/html-to-pdf",
            json={
                "mode": "html",
                "html": "<html><body><h1>Hello</h1></body></html>",
                "page_size": "Letter",
                "orientation": "landscape",
                "margin": "narrow",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["job_id"] == "job_html_test"
        db = next(client.app.dependency_overrides[get_db]())
        try:
            job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_html_test").first()
            assert job is not None
            assert job.user_id == user.id
            assert job.job_type == "html_to_pdf"
            assert job.input_file_name == "Pasted HTML"
        finally:
            db.close()


class TestHTMLToPDFTask:
    def test_task_updates_db_lifecycle_on_success(self, monkeypatch, tmp_path, client):
        from app.core.database import get_db
        from app.domains.jobs.repository import ProcessingJobRepository
        from app.domains.jobs.service import JobService
        import app.tasks.html_tasks as html_tasks_module
        from app.models.user import ProcessingJob

        output = tmp_path / "html.pdf"

        def fake_render(**kwargs):
            output.write_bytes(b"%PDF-1.4 html")
            return {
                "success": True,
                "output_path": str(output),
                "file_size": output.stat().st_size,
            }

        monkeypatch.setattr(html_tasks_module, "render_html_to_pdf", fake_render)

        db = next(client.app.dependency_overrides[get_db]())
        try:
            JobService(ProcessingJobRepository(db)).create_pending(
                job_id="job_html_success",
                user_id=None,
                job_type="html_to_pdf",
                input_file_name="Pasted HTML",
                input_file_size=20,
            )
            service = JobService(ProcessingJobRepository(db))
            monkeypatch.setattr(html_tasks_module, "job_lifecycle", service)
            result = html_tasks_module._run_html_to_pdf_with_job_lifecycle(
                job_id="job_html_success",
                operation=lambda: fake_render(),
            )
            job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_html_success").first()
            assert result["output_path"] == str(output)
            assert job.status == "completed"
            assert job.progress == 100
            assert json.loads(job.result_data)["output_path"] == str(output)
            assert job.output_file_url == str(output)
            assert service.route_status_for_job_id("job_html_success")["status"] == "completed"
        finally:
            db.close()
