"""
文件下载与任务状态逻辑测试
验证 get_download_path 的 425/404/422 分支与多文件打包逻辑（用 FakeRedis + stubbed Celery）
"""
import json
import os
import time
import asyncio
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi import UploadFile

from app.services.file_service import file_processing_service


@pytest.fixture(autouse=True)
def clear_redis():
    """每个测试清空 FakeRedis 内存"""
    file_processing_service.redis_client.store.clear()
    yield
    file_processing_service.redis_client.store.clear()


def _put_job(job_id, status_data):
    file_processing_service.redis_client.setex(f"job:{job_id}", 3600, json.dumps(status_data))


class TestDownloadPath:
    def test_job_not_found(self):
        with pytest.raises(HTTPException) as exc:
            file_processing_service.get_download_path("nope")
        assert exc.value.status_code == 404

    def test_job_not_completed_returns_425(self):
        _put_job("job_x", {"job_id": "job_x", "status": "pending",
                           "created_at": time.time(), "updated_at": time.time()})
        with pytest.raises(HTTPException) as exc:
            file_processing_service.get_download_path("job_x")
        # 注意：get_download_path 内部会调用 get_job_status，stub 的 AsyncResult 默认 PENDING
        assert exc.value.status_code == 425

    def test_single_file_output(self, tmp_path):
        out = tmp_path / "merged.pdf"
        out.write_bytes(b"%PDF-1.4 test")
        _put_job("job_ok", {
            "job_id": "job_ok", "status": "completed",
            "result": {"output_path": str(out)},
            "created_at": time.time(), "updated_at": time.time(),
        })
        path = file_processing_service.get_download_path("job_ok")
        assert str(path) == str(out)
        assert path.exists()

    def test_multi_file_output_zipped(self, tmp_path):
        f1 = tmp_path / "split_1.pdf"; f1.write_bytes(b"%PDF-1.4 a")
        f2 = tmp_path / "split_2.pdf"; f2.write_bytes(b"%PDF-1.4 b")
        _put_job("job_zip", {
            "job_id": "job_zip", "status": "completed",
            "result": {"output_files": [str(f1), str(f2)]},
            "created_at": time.time(), "updated_at": time.time(),
        })
        path = file_processing_service.get_download_path("job_zip")
        assert path.suffix == ".zip"
        assert path.exists()
        import zipfile
        with zipfile.ZipFile(path) as zf:
            assert set(zf.namelist()) == {"split_1.pdf", "split_2.pdf"}

    def test_ocr_text_output(self):
        _put_job("job_ocr", {
            "job_id": "job_ocr", "status": "completed",
            "result": {"text": "hello world"},
            "created_at": time.time(), "updated_at": time.time(),
        })
        path = file_processing_service.get_download_path("job_ocr")
        assert path.suffix == ".txt"
        assert path.read_text(encoding="utf-8") == "hello world"

    def test_failed_job_returns_422(self):
        _put_job("job_fail", {
            "job_id": "job_fail", "status": "failed", "error": "boom",
            "created_at": time.time(), "updated_at": time.time(),
        })
        with pytest.raises(HTTPException) as exc:
            file_processing_service.get_download_path("job_fail")
        assert exc.value.status_code == 422


class TestJobCancellation:
    def test_cancel_pending_job_marks_redis_state_cancelled(self):
        _put_job("job_cancel", {
            "job_id": "job_cancel",
            "status": "pending",
            "progress": 10,
            "created_at": time.time(),
            "updated_at": time.time(),
        })

        result = file_processing_service.cancel_job("job_cancel")

        assert result["status"] == "cancelled"
        assert result["error"] == "Job cancelled by user"
        assert file_processing_service.get_job_status("job_cancel")["status"] == "cancelled"

    def test_cancel_completed_job_returns_409(self):
        _put_job("job_done", {
            "job_id": "job_done",
            "status": "completed",
            "result": {"text": "done"},
            "created_at": time.time(),
            "updated_at": time.time(),
        })

        with pytest.raises(HTTPException) as exc:
            file_processing_service.cancel_job("job_done")

        assert exc.value.status_code == 409

    def test_cancel_job_endpoint_updates_status(self, client):
        _put_job("job_api_cancel", {
            "job_id": "job_api_cancel",
            "status": "pending",
            "created_at": time.time(),
            "updated_at": time.time(),
        })

        cancelled = client.delete("/api/v1/files/jobs/job_api_cancel")

        assert cancelled.status_code == 204
        status_response = client.get("/api/v1/files/jobs/job_api_cancel")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "cancelled"

    def test_status_endpoint_keeps_redis_first_when_db_job_exists(self, client):
        from app.core.database import get_db
        from app.models.user import ProcessingJob

        _put_job("job_status_redis_first", {
            "job_id": "job_status_redis_first",
            "status": "pending",
            "progress": 10,
            "created_at": 100.0,
            "updated_at": 101.0,
        })

        db = next(client.app.dependency_overrides[get_db]())
        try:
            db.add(ProcessingJob(
                job_id="job_status_redis_first",
                user_id=None,
                job_type="compress_pdf",
                status="completed",
                progress=100,
                input_file_name="source.pdf",
                input_file_size=123,
                result_data='{"output_path": "/tmp/result.pdf"}',
                output_file_url="/tmp/result.pdf",
            ))
            db.commit()

            response = client.get("/api/v1/files/jobs/job_status_redis_first")
            assert response.status_code == 200
            body = response.json()
            assert set(body.keys()) == {
                "job_id",
                "status",
                "created_at",
                "updated_at",
                "progress",
                "result",
                "error",
            }
            assert body["status"] == "pending"
            assert body["progress"] == 10
            assert body["result"] is None
        finally:
            db.close()

    def test_status_endpoint_falls_back_to_durable_db_job_when_redis_missing(self, client):
        from datetime import datetime

        from app.core.database import get_db
        from app.models.user import ProcessingJob
        from app.services import file_service as file_service_module
        from conftest import TestingSessionLocal

        created_at = datetime(2026, 1, 2, 3, 4, 5)
        completed_at = datetime(2026, 1, 2, 3, 5, 6)
        db = next(client.app.dependency_overrides[get_db]())
        previous_factory = file_service_module.file_processing_service._db_session_factory
        try:
            file_service_module.file_processing_service._db_session_factory = TestingSessionLocal
            db.add(ProcessingJob(
                job_id="job_status_db_fallback",
                user_id=None,
                job_type="ocr_pdf",
                status="completed",
                progress=100,
                input_file_name="ocr.png",
                input_file_size=321,
                result_data='{"text": "hello"}',
                created_at=created_at,
                completed_at=completed_at,
            ))
            db.commit()

            response = client.get("/api/v1/files/jobs/job_status_db_fallback")
            assert response.status_code == 200
            body = response.json()
            assert set(body.keys()) == {
                "job_id",
                "status",
                "created_at",
                "updated_at",
                "progress",
                "result",
                "error",
            }
            assert body == {
                "job_id": "job_status_db_fallback",
                "status": "completed",
                "created_at": created_at.timestamp(),
                "updated_at": completed_at.timestamp(),
                "progress": 100.0,
                "result": {"text": "hello"},
                "error": None,
            }
        finally:
            file_service_module.file_processing_service._db_session_factory = previous_factory
            db.close()


class TestFileDomain:
    def test_upload_tier_maps_admin_to_enterprise_and_anonymous_to_free(self, client):
        from app.domains.files.service import user_upload_tier
        from app.models.user import User, UserRole

        assert user_upload_tier(None) == "free"
        assert user_upload_tier(User(email="free@example.com", role=UserRole.FREE)) == "free"
        assert user_upload_tier(User(email="admin@example.com", role=UserRole.ADMIN)) == "enterprise"

    def test_validate_office_upload_accepts_known_extensions_and_rejects_unknown(self):
        from app.domains.files.service import validate_office_upload

        docx = UploadFile(filename="report.DOCX", file=BytesIO(b"docx"))
        assert validate_office_upload(docx) == ".docx"

        exe = UploadFile(filename="report.exe", file=BytesIO(b"exe"))
        with pytest.raises(HTTPException) as exc:
            validate_office_upload(exe)
        assert exc.value.status_code == 400
        assert ".docx" in exc.value.detail

    def test_require_job_status_raises_route_compatible_404(self):
        from app.domains.files.service import require_job_status

        with pytest.raises(HTTPException) as exc:
            require_job_status("job_missing", None)

        assert exc.value.status_code == 404
        assert exc.value.detail == "Job not found: job_missing"

    def test_sync_cancelled_processing_job_updates_non_terminal_db_job(self, client):
        from app.core.database import get_db
        from app.domains.files.service import sync_cancelled_processing_job
        from app.models.user import ProcessingJob, User

        db = next(client.app.dependency_overrides[get_db]())
        try:
            user = User(
                email="file-domain@example.com",
                hashed_password="hash",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            job = ProcessingJob(
                job_id="job_db_cancel",
                user_id=user.id,
                job_type="ocr",
                status="processing",
                input_file_name="input.pdf",
                input_file_size=100,
            )
            db.add(job)
            db.commit()

            synced = sync_cancelled_processing_job(db, "job_db_cancel")

            assert synced.status == "cancelled"
            assert synced.error_message == "Job cancelled by user"
            assert synced.completed_at is not None
        finally:
            db.close()


class TestFileValidator:
    """魔术数字 / 大小限制逻辑（MAX_FILE_SIZE 分级）"""

    def test_tier_size_limits(self):
        from app.utils.file_utils import FileValidator
        assert FileValidator.MAX_FILE_SIZE["free"] < FileValidator.MAX_FILE_SIZE["pro"]
        assert FileValidator.MAX_FILE_SIZE["pro"] < FileValidator.MAX_FILE_SIZE["enterprise"]

    def test_allowed_mime_includes_pdf(self):
        from app.utils.file_utils import FileValidator
        assert "application/pdf" in FileValidator.ALLOWED_MIME_TYPES

    def test_allows_ooxml_when_magic_reports_zip(self, monkeypatch):
        from app.utils import file_utils

        monkeypatch.setattr(file_utils.magic, "from_buffer", lambda *_args, **_kwargs: "application/zip")
        upload = UploadFile(filename="sample.docx", file=BytesIO(b"PK\x03\x04valid-docx-content"))

        is_valid, error = asyncio.run(
            file_utils.FileValidator.validate_file(upload, file_utils.FileValidator.MAX_FILE_SIZE["free"])
        )

        assert is_valid is True
        assert error is None

    def test_rejects_generic_zip_upload(self, monkeypatch):
        from app.utils import file_utils

        monkeypatch.setattr(file_utils.magic, "from_buffer", lambda *_args, **_kwargs: "application/zip")
        upload = UploadFile(filename="sample.zip", file=BytesIO(b"PK\x03\x04generic-zip-content"))

        is_valid, error = asyncio.run(
            file_utils.FileValidator.validate_file(upload, file_utils.FileValidator.MAX_FILE_SIZE["free"])
        )

        assert is_valid is False
        assert error == "File type not allowed: application/zip"


class TestFileManager:
    def test_default_base_dir_uses_configured_upload_dir(self):
        from app.core.config import settings
        from app.utils.file_utils import FileManager

        manager = FileManager()
        assert str(manager.base_dir) == settings.UPLOAD_DIR


class TestUploadEndpoint:
    def test_upload_allows_anonymous_user(self, client):
        files = {"file": ("sample.pdf", b"%PDF-1.4\n%test\n", "application/pdf")}
        r = client.post("/api/v1/files/upload", files=files)
        assert r.status_code == 201
        body = r.json()
        assert body["filename"] == "sample.pdf"
        assert body["mime_type"] == "application/pdf"
        assert body["file_id"].startswith("file_")

    def test_upload_allows_authenticated_user(self, client):
        client.post("/api/v1/auth/register", json={
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
        })
        login = client.post("/api/v1/auth/login", data={
            "username": "user@example.com",
            "password": "SecurePass123!",
        })
        token = login.json()["access_token"]

        files = {"file": ("sample.pdf", b"%PDF-1.4\n%test\n", "application/pdf")}
        r = client.post(
            "/api/v1/files/upload",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201
        assert r.json()["file_id"].startswith("file_")


class TestJobHistoryEndpoint:
    def _register_and_login(self, client, email: str) -> str:
        client.post("/api/v1/auth/register", json={
            "email": email,
            "password": "SecurePass123!",
            "full_name": "History User",
        })
        login = client.post("/api/v1/auth/login", data={
            "username": email,
            "password": "SecurePass123!",
        })
        return login.json()["access_token"]

    def _user_id_for_email(self, client, email: str) -> int:
        from app.core.database import get_db
        from app.models.user import User

        db = next(client.app.dependency_overrides[get_db]())
        try:
            return db.query(User).filter(User.email == email).first().id
        finally:
            db.close()

    def test_history_requires_login(self, client):
        response = client.get("/api/v1/files/history")
        assert response.status_code == 401

    def test_history_lists_only_current_user_jobs(self, client, tmp_path):
        from app.core.database import get_db
        from app.models.user import ProcessingJob

        owner_token = self._register_and_login(client, "history-owner@example.com")
        other_token = self._register_and_login(client, "history-other@example.com")
        owner_id = self._user_id_for_email(client, "history-owner@example.com")
        other_id = self._user_id_for_email(client, "history-other@example.com")

        output = tmp_path / "owned.pdf"
        output.write_bytes(b"%PDF-1.4\nowned")

        db = next(client.app.dependency_overrides[get_db]())
        try:
            db.add_all([
                ProcessingJob(
                    job_id="job_history_owner",
                    user_id=owner_id,
                    job_type="compress_pdf",
                    status="completed",
                    progress=100,
                    input_file_name="owned.pdf",
                    input_file_size=12,
                    output_file_url=str(output),
                    result_data=json.dumps({"output_path": str(output)}),
                ),
                ProcessingJob(
                    job_id="job_history_other",
                    user_id=other_id,
                    job_type="merge_pdf",
                    status="completed",
                    progress=100,
                    input_file_name="other.pdf",
                    input_file_size=12,
                    result_data=json.dumps({"output_path": str(output)}),
                ),
            ])
            db.commit()
        finally:
            db.close()

        owner_response = client.get(
            "/api/v1/files/history",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert owner_response.status_code == 200
        body = owner_response.json()
        assert body["total"] == 1
        assert body["items"][0]["job_id"] == "job_history_owner"
        assert body["items"][0]["download_state"] == "available"

        other_detail = client.get(
            "/api/v1/files/history/job_history_owner",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert other_detail.status_code == 404

    def test_completed_history_job_can_download_when_artifact_exists(self, client, tmp_path):
        from app.core.database import get_db
        from app.models.user import ProcessingJob

        token = self._register_and_login(client, "history-download@example.com")
        user_id = self._user_id_for_email(client, "history-download@example.com")
        output = tmp_path / "download.pdf"
        output.write_bytes(b"%PDF-1.4\ndownload")
        now = time.time()
        _put_job("job_history_download", {
            "job_id": "job_history_download",
            "status": "completed",
            "created_at": now,
            "updated_at": now,
            "progress": 100,
            "result": {"output_path": str(output)},
        })

        db = next(client.app.dependency_overrides[get_db]())
        try:
            db.add(ProcessingJob(
                job_id="job_history_download",
                user_id=user_id,
                job_type="compress_pdf",
                status="completed",
                progress=100,
                input_file_name="download.pdf",
                input_file_size=output.stat().st_size,
                output_file_url=str(output),
                result_data=json.dumps({"output_path": str(output)}),
            ))
            db.commit()
        finally:
            db.close()

        response = client.get(
            "/api/v1/files/history/job_history_download/download",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.content == output.read_bytes()

    def test_failed_history_job_is_not_downloadable(self, client):
        from app.core.database import get_db
        from app.models.user import ProcessingJob

        token = self._register_and_login(client, "history-failed@example.com")
        user_id = self._user_id_for_email(client, "history-failed@example.com")

        db = next(client.app.dependency_overrides[get_db]())
        try:
            db.add(ProcessingJob(
                job_id="job_history_failed",
                user_id=user_id,
                job_type="ocr_pdf",
                status="failed",
                progress=20,
                input_file_name="failed.pdf",
                input_file_size=100,
                error_message="Conversion failed\nTraceback should not be shown",
            ))
            db.commit()
        finally:
            db.close()

        detail = client.get(
            "/api/v1/files/history/job_history_failed",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert detail.status_code == 200
        body = detail.json()
        assert body["download_state"] == "unavailable"
        assert body["error_message"] == "Conversion failed"

        download = client.get(
            "/api/v1/files/history/job_history_failed/download",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert download.status_code == 409

    def test_completed_history_job_without_artifact_is_expired(self, client, tmp_path):
        from app.core.database import get_db
        from app.models.user import ProcessingJob

        token = self._register_and_login(client, "history-expired@example.com")
        user_id = self._user_id_for_email(client, "history-expired@example.com")
        missing = tmp_path / "missing.pdf"

        db = next(client.app.dependency_overrides[get_db]())
        try:
            db.add(ProcessingJob(
                job_id="job_history_expired",
                user_id=user_id,
                job_type="merge_pdf",
                status="completed",
                progress=100,
                input_file_name="missing.pdf",
                input_file_size=100,
                output_file_url=str(missing),
                result_data=json.dumps({"output_path": str(missing)}),
            ))
            db.commit()
        finally:
            db.close()

        detail = client.get(
            "/api/v1/files/history/job_history_expired",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert detail.status_code == 200
        assert detail.json()["download_state"] == "expired"

        download = client.get(
            "/api/v1/files/history/job_history_expired/download",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert download.status_code == 410


class TestOfficeToPdfFlow:
    def test_compress_service_creates_anonymous_durable_job(self, monkeypatch, tmp_path, client):
        from app.core.database import get_db
        from app.models.user import ProcessingJob
        from app.services import file_service as file_service_module

        uploaded = tmp_path / "source.pdf"
        uploaded.write_bytes(b"%PDF-1.4 source")
        saved_jobs = {}

        class FakeTask:
            def apply_async(self, args, task_id):
                return MagicMock(id=task_id)

        monkeypatch.setattr(file_service_module.file_processing_service, "_generate_job_id", lambda: "job_compress_db")
        monkeypatch.setattr(
            file_service_module.file_processing_service,
            "_get_file_metadata",
            lambda file_id: {
                "file_id": file_id,
                "filename": "source.pdf",
                "filepath": str(uploaded),
                "size": uploaded.stat().st_size,
            },
        )
        monkeypatch.setattr(
            file_service_module.file_processing_service,
            "_save_job_status",
            lambda job_id, status_data: saved_jobs.setdefault(job_id, status_data),
        )
        monkeypatch.setattr(file_service_module, "compress_pdf_task", FakeTask())

        db = next(client.app.dependency_overrides[get_db]())
        try:
            result = asyncio.run(file_service_module.file_processing_service.compress_pdf("file_compress", db=db))
            db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_compress_db").first()
            assert db_job is not None
            assert db_job.user_id is None
            assert db_job.job_type == "compress_pdf"
            assert db_job.status == "pending"
            assert db_job.input_file_name == "source.pdf"
            assert db_job.input_file_size == uploaded.stat().st_size
            assert result == {
                "job_id": "job_compress_db",
                "status": "pending",
                "message": "PDF compression job queued",
            }
            assert saved_jobs["job_compress_db"]["status"] == "pending"
        finally:
            db.close()

    def test_compress_db_write_failure_does_not_break_redis_flow(self, monkeypatch, tmp_path):
        from app.services import file_service as file_service_module

        uploaded = tmp_path / "source.pdf"
        uploaded.write_bytes(b"%PDF-1.4 source")
        saved_jobs = {}

        class FakeTask:
            def apply_async(self, args, task_id):
                return MagicMock(id=task_id)

        monkeypatch.setattr(file_service_module.file_processing_service, "_generate_job_id", lambda: "job_compress_fallback")
        monkeypatch.setattr(
            file_service_module.file_processing_service,
            "_get_file_metadata",
            lambda file_id: {
                "file_id": file_id,
                "filename": "source.pdf",
                "filepath": str(uploaded),
                "size": uploaded.stat().st_size,
            },
        )
        monkeypatch.setattr(
            file_service_module.file_processing_service,
            "_save_job_status",
            lambda job_id, status_data: saved_jobs.setdefault(job_id, status_data),
        )
        monkeypatch.setattr(file_service_module, "compress_pdf_task", FakeTask())
        monkeypatch.setattr(
            file_service_module.job_lifecycle,
            "create_pending",
            lambda **_kwargs: None,
        )

        result = asyncio.run(file_service_module.file_processing_service.compress_pdf("file_compress"))

        assert result["job_id"] == "job_compress_fallback"
        assert result["status"] == "pending"
        assert saved_jobs["job_compress_fallback"]["status"] == "pending"

    def test_local_pdf_services_create_durable_jobs_and_keep_redis_contract(
        self,
        monkeypatch,
        tmp_path,
        client,
    ):
        from app.core.database import get_db
        from app.models.user import ProcessingJob
        from app.services import file_service as file_service_module

        saved_jobs = {}
        created_tasks = {}

        class FakeTask:
            def __init__(self, label):
                self.label = label

            def apply_async(self, args, task_id):
                created_tasks[self.label] = {"args": args, "task_id": task_id}
                return MagicMock(id=task_id)

        paths = {}
        for file_id, filename, content in [
            ("file_a", "a.pdf", b"%PDF-1.4 a"),
            ("file_b", "b.pdf", b"%PDF-1.4 b"),
            ("file_image", "image.png", b"png"),
        ]:
            path = tmp_path / filename
            path.write_bytes(content)
            paths[file_id] = path

        metadata = {
            file_id: {
                "file_id": file_id,
                "filename": path.name,
                "filepath": str(path),
                "size": path.stat().st_size,
            }
            for file_id, path in paths.items()
        }
        job_ids = iter([
            "job_merge_test",
            "job_split_test",
            "job_rotate_test",
            "job_img2pdf_test",
            "job_pdf2img_test",
        ])

        monkeypatch.setattr(file_service_module.file_processing_service, "_generate_job_id", lambda: next(job_ids))
        monkeypatch.setattr(
            file_service_module.file_processing_service,
            "_get_file_metadata",
            lambda file_id: metadata[file_id],
        )
        monkeypatch.setattr(
            file_service_module.file_processing_service,
            "_save_job_status",
            lambda job_id, status_data: saved_jobs.setdefault(job_id, status_data),
        )
        monkeypatch.setattr(file_service_module, "merge_pdfs_task", FakeTask("merge"))
        monkeypatch.setattr(file_service_module, "split_pdf_task", FakeTask("split"))
        monkeypatch.setattr(file_service_module, "rotate_pdf_task", FakeTask("rotate"))
        monkeypatch.setattr(file_service_module, "convert_images_to_pdf_task", FakeTask("image_to_pdf"))
        monkeypatch.setattr(file_service_module, "convert_pdf_to_images_task", FakeTask("pdf_to_image"))

        db = next(client.app.dependency_overrides[get_db]())
        try:
            results = [
                asyncio.run(file_service_module.file_processing_service.merge_pdfs(["file_a", "file_b"], db=db)),
                asyncio.run(file_service_module.file_processing_service.split_pdf("file_a", [[1, 1]], db=db)),
                asyncio.run(file_service_module.file_processing_service.rotate_pdf("file_a", 90, db=db)),
                asyncio.run(file_service_module.file_processing_service.images_to_pdf(["file_image"], db=db)),
                asyncio.run(file_service_module.file_processing_service.pdf_to_images("file_a", db=db)),
            ]
            expected_types = {
                "job_merge_test": "merge_pdf",
                "job_split_test": "split_pdf",
                "job_rotate_test": "rotate_pdf",
                "job_img2pdf_test": "image_to_pdf",
                "job_pdf2img_test": "pdf_to_image",
            }

            for result in results:
                assert result["status"] == "pending"
                assert saved_jobs[result["job_id"]]["job_id"] == result["job_id"]
                assert saved_jobs[result["job_id"]]["status"] == "pending"
                assert set(saved_jobs[result["job_id"]]) == {
                    "job_id",
                    "status",
                    "created_at",
                    "updated_at",
                }

            for job_id, job_type in expected_types.items():
                db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == job_id).first()
                assert db_job is not None
                assert db_job.user_id is None
                assert db_job.job_type == job_type
                assert db_job.status == "pending"

            assert created_tasks["merge"]["task_id"] == "job_merge_test"
            assert created_tasks["split"]["task_id"] == "job_split_test"
            assert created_tasks["rotate"]["task_id"] == "job_rotate_test"
            assert created_tasks["image_to_pdf"]["task_id"] == "job_img2pdf_test"
            assert created_tasks["pdf_to_image"]["task_id"] == "job_pdf2img_test"
        finally:
            db.close()

    def test_office_service_saves_job_state(self, monkeypatch, client):
        from app.core.database import get_db
        from app.models.user import ProcessingJob
        from app.services import file_service as file_service_module

        saved_jobs = {}

        async def fake_save_upload_file(_file):
            return "/tmp/pdf-flow/uploads/office_test/sample.docx"

        class FakeTask:
            def apply_async(self, args, task_id):
                return MagicMock(id=task_id)

        monkeypatch.setattr(file_service_module.file_processing_service, "_generate_job_id", lambda: "job_office_test")
        monkeypatch.setattr(
            file_service_module.file_processing_service,
            "_save_job_status",
            lambda job_id, status_data: saved_jobs.setdefault(job_id, status_data),
        )

        import sys
        fake_task_module = type(sys)("app.tasks.office_tasks")
        fake_task_module.office_to_pdf_task = FakeTask()
        monkeypatch.setitem(sys.modules, "app.tasks.office_tasks", fake_task_module)

        monkeypatch.setattr(
            sys.modules["app.utils.file_utils"],
            "save_upload_file",
            fake_save_upload_file,
        )

        upload = UploadFile(filename="sample.docx", file=BytesIO(b"PK\x03\x04docx-content"))
        db = next(client.app.dependency_overrides[get_db]())
        try:
            result = asyncio.run(file_service_module.file_processing_service.office_to_pdf(upload, db=db))
            db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_office_test").first()
            assert db_job is not None
            assert db_job.user_id is None
            assert db_job.job_type == "office_to_pdf"
            assert db_job.status == "pending"
            assert db_job.input_file_name == "sample.docx"
            assert db_job.input_file_size == 0
        finally:
            db.close()

        assert result["job_id"] == "job_office_test"
        assert result["status"] == "pending"
        assert saved_jobs["job_office_test"]["status"] == "pending"

    def test_ocr_service_creates_durable_job_and_keeps_redis_contract(self, monkeypatch, tmp_path, client):
        from app.core.database import get_db
        from app.models.user import ProcessingJob
        from app.services import file_service as file_service_module

        uploaded = tmp_path / "ocr-source.pdf"
        uploaded.write_bytes(b"%PDF-1.4 ocr")
        saved_jobs = {}

        class FakeTask:
            def apply_async(self, args, task_id):
                return MagicMock(id=task_id)

        monkeypatch.setattr(file_service_module.file_processing_service, "_generate_job_id", lambda: "job_ocr_db")
        monkeypatch.setattr(
            file_service_module.file_processing_service,
            "_get_file_metadata",
            lambda file_id: {
                "file_id": file_id,
                "filename": "ocr-source.pdf",
                "filepath": str(uploaded),
                "size": uploaded.stat().st_size,
            },
        )
        monkeypatch.setattr(
            file_service_module.file_processing_service,
            "_save_job_status",
            lambda job_id, status_data: saved_jobs.setdefault(job_id, status_data),
        )
        monkeypatch.setattr(file_service_module, "extract_text_task", FakeTask())

        db = next(client.app.dependency_overrides[get_db]())
        try:
            result = asyncio.run(file_service_module.file_processing_service.extract_text_ocr("file_ocr", db=db))
            db_job = db.query(ProcessingJob).filter(ProcessingJob.job_id == "job_ocr_db").first()
            assert db_job is not None
            assert db_job.user_id is None
            assert db_job.job_type == "ocr_pdf"
            assert db_job.status == "pending"
            assert db_job.input_file_name == "ocr-source.pdf"
            assert db_job.input_file_size == uploaded.stat().st_size
        finally:
            db.close()

        assert result == {
            "job_id": "job_ocr_db",
            "status": "pending",
            "message": "OCR job queued",
        }
        assert saved_jobs["job_ocr_db"]["status"] == "pending"
