"""
文件下载与任务状态逻辑测试
验证 get_download_path 的 425/404/422 分支与多文件打包逻辑（用 FakeRedis + stubbed Celery）
"""
import json
import os
import time

import pytest
from fastapi import HTTPException

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


class TestFileValidator:
    """魔术数字 / 大小限制逻辑（MAX_FILE_SIZE 分级）"""

    def test_tier_size_limits(self):
        from app.utils.file_utils import FileValidator
        assert FileValidator.MAX_FILE_SIZE["free"] < FileValidator.MAX_FILE_SIZE["pro"]
        assert FileValidator.MAX_FILE_SIZE["pro"] < FileValidator.MAX_FILE_SIZE["enterprise"]

    def test_allowed_mime_includes_pdf(self):
        from app.utils.file_utils import FileValidator
        assert "application/pdf" in FileValidator.ALLOWED_MIME_TYPES


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
