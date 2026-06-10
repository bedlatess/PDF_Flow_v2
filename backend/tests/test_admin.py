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
