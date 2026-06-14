"""Admin-managed OCR/Office/AI service provider config tests."""


def _register(client, email, password="SecurePass123!"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Service Provider Admin"},
    )


def _login(client, email, password="SecurePass123!"):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


def _make_admin(client, email="service-provider-admin@example.com"):
    from app.core.database import get_db
    from app.models.user import User, UserRole

    _register(client, email=email)
    db = next(client.app.dependency_overrides[get_db]())
    try:
        admin = db.query(User).filter(User.email == email).first()
        admin.role = UserRole.ADMIN
        db.commit()
    finally:
        db.close()
    token = _login(client, email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_list_and_save_local_service_provider_without_secret_leak(client, monkeypatch):
    from app.core.database import get_db
    from app.domains.service_provider.config_store import get_service_provider_runtime_config
    from app.models.user import AdminAuditLog, ServiceProviderConfig

    monkeypatch.setattr("app.domains.service_provider.config_store._command_exists", lambda command: True)
    headers = _make_admin(client)

    listed = client.get("/api/v1/admin/service-provider-configs/ocr", headers=headers)
    assert listed.status_code == 200
    assert [item["provider_key"] for item in listed.json()] == ["local_tesseract"]

    payload = {
        "enabled": True,
        "priority": 50,
        "public_config": {
            "tesseract_path": "/usr/bin/tesseract",
            "default_language": "eng",
            "languages": "eng,chi_sim",
        },
        "secrets": {},
    }
    saved = client.put(
        "/api/v1/admin/service-provider-configs/ocr/local_tesseract",
        headers=headers,
        json=payload,
    )
    assert saved.status_code == 200
    data = saved.json()
    assert data["enabled"] is True
    assert data["priority"] == 50
    assert data["configured"] is True
    assert data["secret_fields"] == {}
    assert data["readiness"]["status"] == "ready"
    assert "secrets" not in data

    db = next(client.app.dependency_overrides[get_db]())
    try:
        row = db.query(ServiceProviderConfig).filter_by(provider_key="local_tesseract").first()
        assert row is not None
        assert row.encrypted_secret_json is None
        runtime = get_service_provider_runtime_config(db, "ocr", "local_tesseract")
        assert runtime is not None
        assert runtime["public_config"]["tesseract_path"] == "/usr/bin/tesseract"
        assert runtime["secrets"] == {}
        audit = db.query(AdminAuditLog).filter_by(
            action="service_provider_config.update",
            target_key="ocr:local_tesseract",
        ).first()
        assert audit is not None
        assert "tesseract_path" in audit.detail
        assert "/usr/bin/tesseract" not in audit.detail
    finally:
        db.close()


def test_disabled_service_provider_falls_back_to_existing_runtime(client, monkeypatch):
    from app.core.database import get_db
    from app.domains.service_provider.config_store import get_service_provider_runtime_config

    monkeypatch.setattr("app.domains.service_provider.config_store._command_exists", lambda command: True)
    headers = _make_admin(client, email="service-provider-disabled@example.com")

    response = client.put(
        "/api/v1/admin/service-provider-configs/office/local_libreoffice",
        headers=headers,
        json={
            "enabled": False,
            "priority": 20,
            "public_config": {
                "binary_path": "libreoffice",
                "timeout_seconds": 30,
            },
            "secrets": {},
        },
    )
    assert response.status_code == 200
    assert response.json()["readiness"]["status"] == "disabled"

    db = next(client.app.dependency_overrides[get_db]())
    try:
        assert get_service_provider_runtime_config(db, "office", "local_libreoffice") is None
    finally:
        db.close()


def test_service_provider_validation_is_local_and_reports_config_errors(client, monkeypatch):
    monkeypatch.setattr("app.domains.service_provider.config_store._command_exists", lambda command: False)
    headers = _make_admin(client, email="service-provider-validate@example.com")

    response = client.post(
        "/api/v1/admin/service-provider-configs/office/local_libreoffice/validate",
        headers=headers,
        json={
            "enabled": True,
            "priority": 100,
            "public_config": {
                "binary_path": "missing-libreoffice",
                "timeout_seconds": 5,
            },
            "secrets": {},
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert "libreoffice_binary_check" in body["checks"]
    assert any("timeout_seconds" in error for error in body["errors"])
    assert any("libreoffice binary" in error for error in body["errors"])


def test_admin_can_save_ai_provider_secret_without_plaintext_leak(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.domains.service_provider.config_store import get_service_provider_runtime_config
    from app.models.user import AdminAuditLog, ServiceProviderConfig

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-service-config-key")
    monkeypatch.setattr("app.domains.service_provider.config_store.GEMINI_SDK_AVAILABLE", True)
    headers = _make_admin(client, email="service-provider-ai@example.com")

    listed = client.get("/api/v1/admin/service-provider-configs/ai", headers=headers)
    assert listed.status_code == 200
    assert [item["provider_key"] for item in listed.json()] == ["google_gemini"]

    secret = "gemini-secret-123456"
    payload = {
        "enabled": True,
        "priority": 40,
        "public_config": {
            "api_base_url": "",
            "model": "gemini-1.5-flash",
            "timeout_seconds": 45,
        },
        "secrets": {"api_key": secret},
    }
    saved = client.put(
        "/api/v1/admin/service-provider-configs/ai/google_gemini",
        headers=headers,
        json=payload,
    )
    assert saved.status_code == 200
    data = saved.json()
    assert data["enabled"] is True
    assert data["configured"] is True
    assert data["secret_fields"]["api_key"] == {"configured": True, "tail": "3456"}
    assert data["readiness"]["status"] == "ready"
    assert "secrets" not in data
    assert secret not in saved.text

    db = next(client.app.dependency_overrides[get_db]())
    try:
        row = db.query(ServiceProviderConfig).filter_by(provider_key="google_gemini").first()
        assert row is not None
        assert row.encrypted_secret_json
        assert secret not in row.encrypted_secret_json
        runtime = get_service_provider_runtime_config(db, "ai", "google_gemini")
        assert runtime is not None
        assert runtime["public_config"]["model"] == "gemini-1.5-flash"
        assert runtime["secrets"]["api_key"] == secret
        audit = db.query(AdminAuditLog).filter_by(
            action="service_provider_config.update",
            target_key="ai:google_gemini",
        ).first()
        assert audit is not None
        assert "api_key" in audit.detail
        assert secret not in audit.detail
    finally:
        db.close()


def test_ai_provider_blank_secret_preserves_existing_secret(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.domains.service_provider.config_store import get_service_provider_runtime_config

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-service-config-key")
    monkeypatch.setattr("app.domains.service_provider.config_store.GEMINI_SDK_AVAILABLE", True)
    headers = _make_admin(client, email="service-provider-ai-preserve@example.com")

    first = client.put(
        "/api/v1/admin/service-provider-configs/ai/google_gemini",
        headers=headers,
        json={
            "enabled": True,
            "priority": 41,
            "public_config": {
                "api_base_url": "",
                "model": "gemini-1.5-pro",
                "timeout_seconds": 60,
            },
            "secrets": {"api_key": "old-gemini-secret"},
        },
    )
    assert first.status_code == 200

    second = client.put(
        "/api/v1/admin/service-provider-configs/ai/google_gemini",
        headers=headers,
        json={
            "enabled": True,
            "priority": 42,
            "public_config": {
                "api_base_url": "",
                "model": "gemini-1.5-pro",
                "timeout_seconds": 70,
            },
            "secrets": {"api_key": ""},
        },
    )
    assert second.status_code == 200
    body = second.json()
    assert body["priority"] == 42
    assert body["secret_fields"]["api_key"]["configured"] is True
    assert body["secret_fields"]["api_key"]["tail"] == "cret"

    db = next(client.app.dependency_overrides[get_db]())
    try:
        runtime = get_service_provider_runtime_config(db, "ai", "google_gemini")
        assert runtime is not None
        assert runtime["public_config"]["timeout_seconds"] == 70
        assert runtime["secrets"]["api_key"] == "old-gemini-secret"
    finally:
        db.close()


def test_ai_provider_disabled_or_incomplete_falls_back_to_env_runtime(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.domains.service_provider.config_store import get_service_provider_runtime_config

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-service-config-key")
    monkeypatch.setattr("app.domains.service_provider.config_store.GEMINI_SDK_AVAILABLE", True)
    headers = _make_admin(client, email="service-provider-ai-fallback@example.com")

    response = client.put(
        "/api/v1/admin/service-provider-configs/ai/google_gemini",
        headers=headers,
        json={
            "enabled": False,
            "priority": 40,
            "public_config": {
                "api_base_url": "",
                "model": "gemini-1.5-pro",
                "timeout_seconds": 60,
            },
            "secrets": {"api_key": "disabled-secret"},
        },
    )
    assert response.status_code == 200
    assert response.json()["readiness"]["status"] == "disabled"

    db = next(client.app.dependency_overrides[get_db]())
    try:
        assert get_service_provider_runtime_config(db, "ai", "google_gemini") is None
    finally:
        db.close()
