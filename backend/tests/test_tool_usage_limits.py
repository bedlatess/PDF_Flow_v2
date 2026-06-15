from datetime import datetime


def _register_and_login(client, email="quota@example.com", password="SecurePass123!"):
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Quota User",
    })
    login = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password,
    })
    return login.json()["access_token"]


def _promote_to_admin(client, email):
    from app.core.database import get_db
    from app.models.user import User, UserRole

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = db.query(User).filter(User.email == email).first()
        user.role = UserRole.ADMIN
        db.commit()
    finally:
        db.close()


def _put_uploaded_file(service, file_id, path, filename="source.pdf"):
    import json

    service.redis_client.setex(
        f"file:{file_id}",
        3600,
        json.dumps({
            "file_id": file_id,
            "filename": filename,
            "filepath": str(path),
            "size": path.stat().st_size,
            "mime_type": "application/pdf",
            "upload_time": datetime.utcnow().timestamp(),
            "user_tier": "free",
        }),
    )


def test_admin_can_save_tool_quota_fields_and_audit(client):
    email = "quota-admin@example.com"
    token = _register_and_login(client, email)
    _promote_to_admin(client, email)
    headers = {"Authorization": f"Bearer {token}"}

    flags = client.get("/api/v1/admin/feature-flags", headers=headers)
    assert flags.status_code == 200
    merge = next(flag for flag in flags.json() if flag["key"] == "merge_pdf")

    response = client.put(
        "/api/v1/admin/feature-flags/merge_pdf",
        headers=headers,
        json={
            **merge,
            "free_daily_limit": 1,
            "free_max_file_size_mb": 2,
            "free_batch_file_limit": 3,
            "pro_daily_limit": 50,
            "pro_max_file_size_mb": 100,
            "pro_batch_file_limit": 10,
            "pro_unlimited": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["free_daily_limit"] == 1
    logs = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert "free_daily_limit" in logs.json()[0]["detail"]


def test_free_daily_limit_blocks_task_creation_after_success(client, monkeypatch, tmp_path):
    from app.core.database import get_db
    from app.models.user import FeatureFlag, ToolUsageLog
    from app.services import file_service as file_service_module

    source = tmp_path / "source.pdf"
    source.write_bytes(b"%PDF-1.4 quota")
    _put_uploaded_file(file_service_module.file_processing_service, "file_quota", source)

    db = next(client.app.dependency_overrides[get_db]())
    try:
        db.add(
            FeatureFlag(
                key="compress_pdf",
                label="Compress PDF",
                enabled=True,
                is_public=True,
                requires_login=False,
                requires_pro=False,
                free_daily_limit=1,
                free_max_file_size_mb=10,
                free_batch_file_limit=5,
                pro_daily_limit=100,
                pro_max_file_size_mb=100,
                pro_batch_file_limit=20,
            )
        )
        db.commit()
    finally:
        db.close()

    async def fake_compress(*_args, **_kwargs):
        return {"job_id": "job_quota", "status": "pending", "message": "queued"}

    monkeypatch.setattr(file_service_module.file_processing_service, "compress_pdf", fake_compress)

    first = client.post("/api/v1/files/compress", json={"file_id": "file_quota", "quality": "medium"})
    assert first.status_code == 200
    db = next(client.app.dependency_overrides[get_db]())
    try:
        assert db.query(ToolUsageLog).filter(ToolUsageLog.tool_type == "compress_pdf").count() == 1
    finally:
        db.close()

    blocked = client.post("/api/v1/files/compress", json={"file_id": "file_quota", "quality": "medium"})
    assert blocked.status_code == 403
    assert "Daily conversion limit reached" in blocked.json()["detail"]

    db = next(client.app.dependency_overrides[get_db]())
    try:
        assert db.query(ToolUsageLog).filter(ToolUsageLog.tool_type == "compress_pdf").count() == 1
    finally:
        db.close()


def test_file_size_limit_blocks_before_task_creation(client, monkeypatch, tmp_path):
    from app.core.database import get_db
    from app.models.user import FeatureFlag
    from app.services import file_service as file_service_module

    source = tmp_path / "large.pdf"
    source.write_bytes(b"x" * (2 * 1024 * 1024))
    _put_uploaded_file(file_service_module.file_processing_service, "file_large", source, "large.pdf")

    db = next(client.app.dependency_overrides[get_db]())
    try:
        db.add(
            FeatureFlag(
                key="compress_pdf",
                label="Compress PDF",
                enabled=True,
                is_public=True,
                requires_login=False,
                requires_pro=False,
                free_daily_limit=10,
                free_max_file_size_mb=1,
                free_batch_file_limit=5,
            )
        )
        db.commit()
    finally:
        db.close()

    async def should_not_run(*_args, **_kwargs):
        raise AssertionError("task creation should be blocked")

    monkeypatch.setattr(file_service_module.file_processing_service, "compress_pdf", should_not_run)

    response = client.post("/api/v1/files/compress", json={"file_id": "file_large", "quality": "medium"})
    assert response.status_code == 413
    assert "up to 1 MB" in response.json()["detail"]


def test_history_download_is_not_limited(client, tmp_path):
    from app.core.database import get_db
    from app.models.user import FeatureFlag, ProcessingJob
    from app.services import file_service as file_service_module
    import json

    token = _register_and_login(client, "history-quota@example.com")
    output = tmp_path / "result.pdf"
    output.write_bytes(b"%PDF-1.4 result")

    db = next(client.app.dependency_overrides[get_db]())
    try:
        from app.models.user import User

        user = db.query(User).filter(User.email == "history-quota@example.com").first()
        db.add(
            FeatureFlag(
                key="compress_pdf",
                label="Compress PDF",
                enabled=True,
                is_public=True,
                requires_login=False,
                free_daily_limit=0,
            )
        )
        db.add(
            ProcessingJob(
                job_id="job_history_quota",
                user_id=user.id,
                job_type="compress_pdf",
                status="completed",
                progress=100,
                input_file_name="source.pdf",
                input_file_size=12,
                output_file_url=str(output),
                result_data='{"output_path": "' + str(output).replace("\\", "\\\\") + '"}',
            )
        )
        db.commit()
    finally:
        db.close()
    file_service_module.file_processing_service.redis_client.setex(
        "job:job_history_quota",
        3600,
        json.dumps({
            "job_id": "job_history_quota",
            "status": "completed",
            "progress": 100,
            "result": {"output_path": str(output)},
        }),
    )

    response = client.get(
        "/api/v1/files/history/job_history_quota/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
