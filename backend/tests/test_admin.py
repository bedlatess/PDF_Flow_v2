"""Hidden admin console API tests."""


def _register(client, email="admin@example.com", password="SecurePass123!"):
    return client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Admin User",
    })


def _login(client, email="admin@example.com", password="SecurePass123!"):
    return client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password,
    })


def _promote_to_admin(client, email="admin@example.com"):
    from app.core.database import get_db
    from app.models.user import User, UserRole

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = db.query(User).filter(User.email == email).first()
        user.role = UserRole.ADMIN
        db.commit()
    finally:
        db.close()


def test_admin_overview_requires_admin_role(client):
    _register(client, email="free@example.com")
    token = _login(client, email="free@example.com").json()["access_token"]

    response = client.get(
        "/api/v1/admin/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_can_seed_and_update_feature_flag(client):
    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    overview = client.get("/api/v1/admin/overview", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["feature_flags_count"] >= 1

    flags = client.get("/api/v1/admin/feature-flags", headers=headers)
    assert flags.status_code == 200
    merge_flag = next(flag for flag in flags.json() if flag["key"] == "merge_pdf")

    updated = client.put(
        "/api/v1/admin/feature-flags/merge_pdf",
        headers=headers,
        json={
            "label": merge_flag["label"],
            "description": merge_flag["description"],
            "enabled": False,
            "requires_login": False,
            "requires_pro": False,
            "maintenance_message": "合并功能维护中",
        },
    )

    assert updated.status_code == 200
    assert updated.json()["enabled"] is False
    assert updated.json()["maintenance_message"] == "合并功能维护中"

    logs = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert logs.status_code == 200
    assert logs.json()[0]["target_type"] == "feature_flag"
    assert logs.json()[0]["target_key"] == "merge_pdf"


def test_public_config_exposes_feature_flags(client):
    response = client.get("/api/v1/admin/public-config")

    assert response.status_code == 200
    body = response.json()
    assert "feature_flags" in body
    assert body["settings"]["support_email"]["value"] == "support@pdf-flow.com"
    assert body["feature_flags"]["merge_pdf"]["enabled"] is True
    assert body["content_blocks"]["home_hero:zh"]["content"].startswith("隐私优先")


def test_disabled_feature_blocks_backend_endpoint(client):
    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.get("/api/v1/admin/overview", headers=headers)
    response = client.put(
        "/api/v1/admin/feature-flags/merge_pdf",
        headers=headers,
        json={
            "label": "合并 PDF",
            "description": "允许用户合并多个 PDF 文件。",
            "enabled": False,
            "requires_login": False,
            "requires_pro": False,
            "maintenance_message": "合并功能维护中",
        },
    )
    assert response.status_code == 200

    blocked = client.post(
        "/api/v1/files/merge",
        json={"file_ids": ["file_a", "file_b"], "output_filename": "merged.pdf"},
    )

    assert blocked.status_code == 503
    assert blocked.json()["detail"] == "合并功能维护中"


def test_default_feature_gate_applies_before_admin_seed(client):
    blocked = client.post(
        "/api/v1/files/ocr",
        json={"file_id": "file_ocr", "language": "eng"},
    )

    assert blocked.status_code == 401
    assert blocked.json()["detail"] == "Please sign in to use this feature."


def test_maintenance_mode_blocks_processing_for_non_admin(client):
    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.put(
        "/api/v1/admin/settings/maintenance_mode",
        headers=headers,
        json={
            "value": "true",
            "value_type": "boolean",
            "group": "system",
            "label": "维护模式",
            "description": "测试维护模式",
            "is_public": True,
        },
    )
    assert response.status_code == 200

    message = client.put(
        "/api/v1/admin/settings/global_announcement",
        headers=headers,
        json={
            "value": "系统维护测试中",
            "value_type": "textarea",
            "group": "notice",
            "label": "全站公告",
            "description": "测试公告",
            "is_public": True,
        },
    )
    assert message.status_code == 200

    blocked = client.post(
        "/api/v1/files/merge",
        json={"file_ids": ["file_a", "file_b"], "output_filename": "merged.pdf"},
    )

    assert blocked.status_code == 503
    assert blocked.json()["detail"] == "系统维护测试中"


def test_admin_can_list_and_update_users(client):
    _register(client)
    _promote_to_admin(client)
    _register(client, email="customer@example.com")
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    users = client.get("/api/v1/admin/users", headers=headers)
    assert users.status_code == 200
    customer = next(user for user in users.json() if user["email"] == "customer@example.com")
    assert customer["is_test_account"] is True

    updated = client.patch(
        f"/api/v1/admin/users/{customer['id']}",
        headers=headers,
        json={"role": "pro", "is_verified": True},
    )

    assert updated.status_code == 200
    assert updated.json()["role"] == "pro"
    assert updated.json()["is_verified"] is True

    logs = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert logs.status_code == 200
    assert logs.json()[0]["target_type"] == "user"
    assert logs.json()[0]["target_key"] == "customer@example.com"


def test_admin_cannot_remove_own_admin_access(client):
    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    users = client.get("/api/v1/admin/users", headers=headers).json()
    admin = next(user for user in users if user["email"] == "admin@example.com")

    demote = client.patch(
        f"/api/v1/admin/users/{admin['id']}",
        headers=headers,
        json={"role": "free"},
    )
    deactivate = client.patch(
        f"/api/v1/admin/users/{admin['id']}",
        headers=headers,
        json={"is_active": False},
    )

    assert demote.status_code == 400
    assert deactivate.status_code == 400


def test_admin_can_delete_non_current_user(client):
    _register(client)
    _promote_to_admin(client)
    _register(client, email="remove-me@example.com")
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    users = client.get("/api/v1/admin/users", headers=headers).json()
    target = next(user for user in users if user["email"] == "remove-me@example.com")

    deleted = client.delete(f"/api/v1/admin/users/{target['id']}", headers=headers)
    remaining = client.get("/api/v1/admin/users", headers=headers)

    assert deleted.status_code == 204
    assert all(user["email"] != "remove-me@example.com" for user in remaining.json())


def test_admin_cannot_delete_self(client):
    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    users = client.get("/api/v1/admin/users", headers=headers).json()
    admin = next(user for user in users if user["email"] == "admin@example.com")

    deleted = client.delete(f"/api/v1/admin/users/{admin['id']}", headers=headers)

    assert deleted.status_code == 400


def test_admin_can_list_recent_jobs(client):
    from app.core.database import get_db
    from app.models.user import ProcessingJob, User

    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    db = next(client.app.dependency_overrides[get_db]())
    try:
        user = db.query(User).filter(User.email == "admin@example.com").first()
        db.add(ProcessingJob(
            job_id="job_admin_test",
            user_id=user.id,
            job_type="merge_pdf",
            status="failed",
            progress=25,
            input_file_name="sample.pdf",
            input_file_size=1024,
            error_message="sample failure",
        ))
        db.commit()
    finally:
        db.close()

    jobs = client.get("/api/v1/admin/jobs", headers=headers)

    assert jobs.status_code == 200
    assert jobs.json()[0]["job_id"] == "job_admin_test"
    assert jobs.json()[0]["user_email"] == "admin@example.com"
    assert jobs.json()[0]["status"] == "failed"


def test_admin_can_list_redis_jobs(client):
    from app.services.file_service import file_processing_service

    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    file_processing_service._save_job_status("job_redis_test", {
        "job_id": "job_redis_test",
        "status": "completed",
        "progress": 100,
        "message": "PDF merge job queued",
        "created_at": 1780998441.0,
        "updated_at": 1780998442.0,
        "result": {
            "output_path": "/tmp/pdf-flow/uploads/merged.pdf",
            "file_size": 2048,
        },
    })

    jobs = client.get("/api/v1/admin/jobs", headers=headers)

    assert jobs.status_code == 200
    redis_job = next(job for job in jobs.json() if job["job_id"] == "job_redis_test")
    assert redis_job["job_type"] == "merge_pdf"
    assert redis_job["status"] == "completed"
    assert redis_job["input_file_size"] == 2048


def test_admin_operations_overview_returns_health_and_recent_activity(client):
    from app.services.file_service import file_processing_service

    _register(client)
    _promote_to_admin(client)
    _register(client, email="smoke-ops@example.com")
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    file_processing_service._save_job_status("job_ops_failed", {
        "job_id": "job_ops_failed",
        "status": "failed",
        "progress": 40,
        "message": "OCR job queued",
        "created_at": 1780998443.0,
        "updated_at": 1780998444.0,
        "error": "sample ops failure",
    })

    response = client.get("/api/v1/admin/operations", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["services"]["database"]["status"] == "healthy"
    assert body["services"]["redis"]["status"] == "healthy"
    assert body["total_users"] == 2
    assert body["test_users"] == 2
    assert body["visible_jobs"] >= 1
    assert body["failed_jobs"] >= 1
    assert body["recent_failed_jobs"][0]["job_id"] == "job_ops_failed"


def test_guest_can_submit_feedback_and_admin_can_triage(client):
    response = client.post("/api/v1/feedback", json={
        "title": "PDF conversion failed",
        "message": "The local PDF to image conversion failed on the public site.",
        "email": "tester@example.com",
        "category": "bug",
        "severity": "high",
        "page_url": "https://pdf.pawn.eu.org/tools/pdf-to-image",
        "diagnostic_code": "PDF-FLOW-TEST",
        "diagnostics": {
            "path": "/tools/pdf-to-image",
            "locale": "zh",
            "viewport": "1440x900",
            "secret": "should not be stored",
        },
    })

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "new"
    assert body["diagnostic_code"] == "PDF-FLOW-TEST"

    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    feedback = client.get("/api/v1/admin/feedback", headers=headers)
    assert feedback.status_code == 200
    item = feedback.json()[0]
    assert item["title"] == "PDF conversion failed"
    assert item["email"] == "tester@example.com"
    assert "secret" not in (item["diagnostics"] or "")

    updated = client.patch(
        f"/api/v1/admin/feedback/{item['id']}",
        headers=headers,
        json={"status": "reviewing", "admin_note": "Need browser screenshot."},
    )

    assert updated.status_code == 200
    assert updated.json()["status"] == "reviewing"
    assert updated.json()["admin_note"] == "Need browser screenshot."


def test_feedback_admin_list_requires_admin(client):
    _register(client, email="free-feedback@example.com")
    token = _login(client, email="free-feedback@example.com").json()["access_token"]

    response = client.get(
        "/api/v1/admin/feedback",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_can_observe_api_errors_and_diagnostics(client):
    from fastapi.testclient import TestClient
    from app.main import app

    route_path = "/api/v1/test-observable-error"

    if not any(getattr(route, "path", None) == route_path for route in app.router.routes):
        @app.get(route_path)
        async def _test_observable_error():
            raise RuntimeError("observable test failure")

    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(app, raise_server_exceptions=False) as safe_client:
        failed = safe_client.get(route_path)
        assert failed.status_code == 500

    errors = client.get("/api/v1/admin/errors", headers=headers)
    assert errors.status_code == 200
    assert errors.json()[0]["path"] == route_path
    assert errors.json()[0]["status_code"] == 500

    diagnostics = client.get("/api/v1/admin/diagnostics", headers=headers)
    assert diagnostics.status_code == 200
    body = diagnostics.json()
    assert body["api_error_count"] >= 1
    assert body["recent_errors"][0]["path"] == route_path
