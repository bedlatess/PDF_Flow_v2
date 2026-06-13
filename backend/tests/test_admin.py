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
    assert body["feature_flags"]["delete_pages_pdf"]["enabled"] is True
    assert body["feature_flags"]["organize_pdf"]["enabled"] is True
    assert body["feature_flags"]["page_numbers_pdf"]["enabled"] is True
    assert body["feature_flags"]["crop_pdf"]["enabled"] is True
    assert body["feature_flags"]["crop_pdf"]["requires_login"] is False
    assert body["feature_flags"]["crop_pdf"]["requires_pro"] is False
    assert body["feature_flags"]["flatten_pdf"]["enabled"] is True
    assert body["feature_flags"]["flatten_pdf"]["requires_login"] is False
    assert body["feature_flags"]["flatten_pdf"]["requires_pro"] is False
    assert body["feature_flags"]["repair_pdf"]["enabled"] is True
    assert body["feature_flags"]["repair_pdf"]["requires_login"] is True
    assert body["feature_flags"]["repair_pdf"]["requires_pro"] is False
    assert body["feature_flags"]["protect_pdf"]["enabled"] is True
    assert body["feature_flags"]["protect_pdf"]["requires_login"] is True
    assert body["feature_flags"]["protect_pdf"]["requires_pro"] is False
    assert body["feature_flags"]["unlock_pdf"]["enabled"] is True
    assert body["feature_flags"]["unlock_pdf"]["requires_login"] is True
    assert body["feature_flags"]["unlock_pdf"]["requires_pro"] is False
    assert body["feature_flags"]["sign_pdf"]["enabled"] is True
    assert body["feature_flags"]["sign_pdf"]["requires_login"] is False
    assert body["feature_flags"]["sign_pdf"]["requires_pro"] is False
    assert body["feature_flags"]["extract_text_pdf"]["enabled"] is True
    assert body["feature_flags"]["extract_text_pdf"]["requires_login"] is False
    assert body["feature_flags"]["extract_text_pdf"]["requires_pro"] is False
    assert body["feature_flags"]["extract_images_pdf"]["enabled"] is True
    assert body["feature_flags"]["extract_images_pdf"]["requires_login"] is False
    assert body["feature_flags"]["extract_images_pdf"]["requires_pro"] is False
    assert body["content_blocks"]["home_hero:zh"]["content"].startswith("隐私优先")
    assert body["oauth_providers"]["google"]["enabled"] is False
    assert body["oauth_providers"]["github"]["enabled"] is False


def test_public_config_marks_only_configured_oauth_providers(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", None)
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", None)
    monkeypatch.setattr(settings, "GITHUB_CLIENT_ID", "github-client")
    monkeypatch.setattr(settings, "GITHUB_CLIENT_SECRET", "github-secret")

    response = client.get("/api/v1/admin/public-config")

    assert response.status_code == 200
    providers = response.json()["oauth_providers"]
    assert providers["google"] == {"label": "Google", "enabled": False}
    assert providers["github"] == {"label": "GitHub", "enabled": True}


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


def test_admin_can_create_user_password_reset_link(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "FRONTEND_URL", "https://pdf.pawn.eu.org/")
    monkeypatch.setattr(settings, "PASSWORD_RESET_TOKEN_EXPIRE_HOURS", 2)

    _register(client)
    _promote_to_admin(client)
    _register(client, email="reset-customer@example.com", password="OldSecure123!")
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    users = client.get("/api/v1/admin/users", headers=headers).json()
    customer = next(user for user in users if user["email"] == "reset-customer@example.com")

    response = client.post(
        f"/api/v1/admin/users/{customer['id']}/password-reset-link",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "reset-customer@example.com"
    assert body["reset_url"].startswith(
        "https://pdf.pawn.eu.org/zh-cn/auth/reset-password?token="
    )

    reset_token = body["reset_url"].split("token=", 1)[1]
    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "NewSecure123!"},
    )
    assert reset.status_code == 200
    reused = client.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "AnotherSecure123!"},
    )
    assert reused.status_code == 400
    assert _login(
        client,
        email="reset-customer@example.com",
        password="NewSecure123!",
    ).status_code == 200

    logs = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert logs.status_code == 200
    assert logs.json()[0]["target_type"] == "password_reset_link"
    assert logs.json()[0]["target_key"] == "reset-customer@example.com"


def test_admin_password_reset_link_requires_admin_and_active_user(client):
    _register(client)
    _promote_to_admin(client)
    _register(client, email="inactive-reset@example.com")
    admin_token = _login(client).json()["access_token"]
    free_token = _login(client, email="inactive-reset@example.com").json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    free_headers = {"Authorization": f"Bearer {free_token}"}

    users = client.get("/api/v1/admin/users", headers=admin_headers).json()
    target = next(user for user in users if user["email"] == "inactive-reset@example.com")

    forbidden = client.post(
        f"/api/v1/admin/users/{target['id']}/password-reset-link",
        headers=free_headers,
    )
    assert forbidden.status_code == 403

    disabled = client.patch(
        f"/api/v1/admin/users/{target['id']}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert disabled.status_code == 200

    response = client.post(
        f"/api/v1/admin/users/{target['id']}/password-reset-link",
        headers=admin_headers,
    )
    assert response.status_code == 400


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


def test_admin_can_cleanup_test_users_without_touching_real_accounts(client):
    from app.core.database import get_db
    from app.models.user import FeedbackReport, User

    _register(client)
    _promote_to_admin(client)
    _register(client, email="smoke-clean@example.com")
    real_register = _register(client, email="real-user@pdf-flow.com")
    assert real_register.status_code in (200, 201)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    db = next(client.app.dependency_overrides[get_db]())
    try:
        test_user = db.query(User).filter(User.email == "smoke-clean@example.com").first()
        db.add(FeedbackReport(
            user_id=test_user.id,
            title="test owned feedback",
            message="keep the report but detach user",
        ))
        db.commit()
    finally:
        db.close()

    summary = client.get("/api/v1/admin/maintenance", headers=headers)
    cleaned = client.post("/api/v1/admin/users/cleanup-test-users", headers=headers)
    remaining = client.get("/api/v1/admin/users", headers=headers)

    assert summary.status_code == 200
    assert summary.json()["test_users_count"] == 1
    assert cleaned.status_code == 200
    assert cleaned.json()["deleted_count"] == 1
    emails = [user["email"] for user in remaining.json()]
    assert "smoke-clean@example.com" not in emails
    assert "admin@example.com" in emails
    assert "real-user@pdf-flow.com" in emails

    db = next(client.app.dependency_overrides[get_db]())
    try:
        report = db.query(FeedbackReport).filter(FeedbackReport.title == "test owned feedback").first()
        assert report is not None
        assert report.user_id is None
    finally:
        db.close()


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


def test_admin_health_report_returns_copyable_status(client):
    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/admin/health-report", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["app_version"]
    assert body["environment"]
    assert "database" in body["services"]
    assert "redis" in body["services"]
    assert "users_count" in body
    assert "open_feedback_count" in body
    assert "api_error_count" in body


def test_admin_health_report_requires_admin(client):
    _register(client, email="free-health@example.com")
    token = _login(client, email="free-health@example.com").json()["access_token"]

    response = client.get(
        "/api/v1/admin/health-report",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_payment_operations_requires_admin(client):
    _register(client, email="free-payments@example.com")
    token = _login(client, email="free-payments@example.com").json()["access_token"]

    response = client.get(
        "/api/v1/admin/payments",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_payment_operations_returns_provider_health_and_reconciliation(client, monkeypatch):
    from datetime import datetime, timedelta
    from app.core.config import settings
    from app.core.database import get_db
    from app.models.user import PaymentEvent, PaymentOrder, User

    monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "stripe,epusdt,wechat")
    monkeypatch.setattr(settings, "PAYMENT_GATEWAY_CONFIGS_RAW", "{}")
    monkeypatch.setattr(settings, "BACKEND_PUBLIC_URL", "https://api.pdf-flow.test")
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://app.pdf-flow.test")
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_admin")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_test_admin")
    monkeypatch.setattr(settings, "STRIPE_PRICE_ID_MONTHLY", "price_monthly_admin")
    monkeypatch.setattr(settings, "STRIPE_PRICE_ID_YEARLY", "price_yearly_admin")
    monkeypatch.setattr(settings, "WECHAT_PAY_APP_ID", "wx_admin")
    monkeypatch.setattr(settings, "WECHAT_PAY_MCH_ID", "mch_admin")
    monkeypatch.setattr(settings, "WECHAT_PAY_SERIAL_NO", "serial_admin")
    monkeypatch.setattr(settings, "WECHAT_PAY_PRIVATE_KEY", "private_key_admin")
    monkeypatch.setattr(settings, "WECHAT_PAY_API_V3_KEY", "api_v3_admin")
    monkeypatch.setattr(settings, "WECHAT_PAY_PLATFORM_CERT", "platform_cert_admin")

    _register(client)
    _promote_to_admin(client)
    _register(client, email="paying-customer@example.com")
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    db = next(client.app.dependency_overrides[get_db]())
    try:
        payer = db.query(User).filter(User.email == "paying-customer@example.com").first()
        db.add_all([
            PaymentOrder(
                user_id=payer.id,
                provider="stripe",
                merchant_order_id="pf_admin_paid",
                provider_order_id="cs_paid",
                plan="monthly",
                amount_cents=990,
                currency="USD",
                status="paid",
                checkout_url="https://checkout.stripe.local/session",
                paid_at=datetime.utcnow(),
            ),
            PaymentOrder(
                user_id=payer.id,
                provider="epusdt",
                merchant_order_id="pf_admin_pending",
                provider_order_id="usdt_pending",
                plan="yearly",
                amount_cents=7900,
                currency="USD",
                status="pending",
                qr_code_url="tron:private-payment-address",
                expires_at=datetime.utcnow() - timedelta(minutes=5),
            ),
            PaymentOrder(
                user_id=payer.id,
                provider="wechat",
                merchant_order_id="pf_admin_mismatch",
                provider_order_id="wx_mismatch",
                plan="monthly",
                amount_cents=990,
                currency="CNY",
                status="amount_mismatch",
            ),
        ])
        db.commit()
        paid_order = db.query(PaymentOrder).filter(
            PaymentOrder.merchant_order_id == "pf_admin_paid"
        ).first()
        db.add(PaymentEvent(
            order_id=paid_order.id,
            provider="stripe",
            provider_event_id="evt_admin_paid",
            merchant_order_id="pf_admin_paid",
            provider_order_id="cs_paid",
            event_type="paid",
            processing_status="applied",
            amount_cents=990,
            currency="USD",
            raw_summary='{"type":"checkout.session.completed"}',
        ))
        db.commit()
    finally:
        db.close()

    response = client.get("/api/v1/admin/payments", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_orders"] == 3
    assert body["paid_orders"] == 1
    assert body["pending_orders"] == 1
    assert body["amount_mismatch_orders"] == 1
    assert body["expired_pending_orders"] == 1
    assert body["paid_amount_cents"] == 990
    assert body["currency_breakdown"]["USD"] == 990

    stripe = next(provider for provider in body["providers"] if provider["key"] == "stripe")
    epusdt = next(provider for provider in body["providers"] if provider["key"] == "epusdt")
    assert stripe["enabled"] is True
    assert stripe["paid_orders"] == 1
    assert stripe["acceptance_status"] == "accepted"
    assert stripe["acceptance_label"] == "Smoke passed"
    assert stripe["acceptance_blockers"] == []
    assert stripe["latest_paid_event_at"] is not None
    assert stripe["webhook_url"] == "https://api.pdf-flow.test/api/v1/payment/webhooks/stripe"
    assert stripe["success_return_url"] == "https://app.pdf-flow.test/payment/success"
    assert "STRIPE_WEBHOOK_SECRET" in stripe["required_config_keys"]
    assert "checkout.session.completed webhook" in " ".join(stripe["sandbox_runbook"])
    assert "PaymentEvent processing_status=applied" in " ".join(stripe["expected_event_flow"])
    assert epusdt["enabled"] is True
    assert epusdt["configured"] is False
    assert epusdt["acceptance_status"] == "missing_config"
    assert "PAYMENT_GATEWAY_CONFIGS.epusdt.secret" in epusdt["acceptance_blockers"]
    assert epusdt["open_orders"] == 1
    assert epusdt["webhook_url"] == "https://api.pdf-flow.test/api/v1/payment/webhooks/epusdt"
    assert "PAYMENT_GATEWAY_CONFIGS.epusdt.secret" in epusdt["missing_config_keys"]
    assert "EPUSDT" in epusdt["merchant_console_hint"]
    assert "USDT test order" in " ".join(epusdt["sandbox_runbook"])
    assert "gateway trade id" in epusdt["evidence_fields"]

    wechat = next(provider for provider in body["providers"] if provider["key"] == "wechat")
    assert wechat["acceptance_status"] == "needs_review"
    assert "manual review" in " ".join(wechat["acceptance_blockers"])
    assert "API v3" in " ".join(wechat["go_live_checklist"])
    assert "platform certificate" in " ".join(wechat["troubleshooting_steps"])

    order = next(item for item in body["recent_orders"] if item["merchant_order_id"] == "pf_admin_paid")
    assert order["user_email"] == "paying-customer@example.com"
    assert order["checkout_url_present"] is True
    assert "checkout.stripe.local" not in body["reconciliation_summary"]
    assert "tron:private-payment-address" not in body["reconciliation_summary"]
    assert "Privacy note" in body["reconciliation_summary"]
    assert "PDF-Flow payment integration evidence packet" in body["integration_evidence_packet"]
    assert "acceptance_status=accepted" in body["integration_evidence_packet"]
    assert "acceptance_status=missing_config" in body["integration_evidence_packet"]
    assert "provider_dashboard_event_url=" in body["integration_evidence_packet"]
    assert "evt_admin_paid" in body["integration_evidence_packet"]
    assert "checkout.stripe.local" not in body["integration_evidence_packet"]
    assert "tron:private-payment-address" not in body["integration_evidence_packet"]
    assert "raw provider payloads" in body["integration_evidence_packet"]

    filtered = client.get(
        "/api/v1/admin/payments",
        headers=headers,
        params={"provider": "epusdt", "status_filter": "pending"},
    )
    assert filtered.status_code == 200
    assert [item["provider"] for item in filtered.json()["recent_orders"]] == ["epusdt"]


def test_guest_can_submit_feedback_and_admin_can_triage(client):
    long_url = f"https://pdf.pawn.eu.org/tools/pdf-to-image?debug={'x' * 1500}"
    response = client.post("/api/v1/feedback", json={
        "title": "PDF conversion failed",
        "message": "The local PDF to image conversion failed on the public site.",
        "email": "tester@example.com",
        "category": "bug",
        "severity": "high",
        "page_url": long_url,
        "diagnostic_code": "PDF-FLOW-TEST",
        "diagnostics": {
            "path": "/tools/pdf-to-image",
            "locale": "zh",
            "viewport": "1440x900",
            "url": long_url,
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
    assert len(item["page_url"]) <= 1200
    assert len(item["diagnostics"]) < len(long_url)

    updated = client.patch(
        f"/api/v1/admin/feedback/{item['id']}",
        headers=headers,
        json={"status": "reviewing", "admin_note": "Need browser screenshot."},
    )

    assert updated.status_code == 200
    assert updated.json()["status"] == "reviewing"
    assert updated.json()["admin_note"] == "Need browser screenshot."


def test_feedback_message_length_is_enforced(client):
    accepted = client.post("/api/v1/feedback", json={
        "title": "Long but valid feedback",
        "message": "x" * 4000,
    })
    rejected = client.post("/api/v1/feedback", json={
        "title": "Too long feedback",
        "message": "x" * 4001,
    })

    assert accepted.status_code == 200
    assert rejected.status_code == 422


def test_admin_can_cleanup_live_acceptance_feedback_only(client):
    client.post("/api/v1/feedback", json={
        "title": "live acceptance 123",
        "message": "synthetic probe",
    })
    client.post("/api/v1/feedback", json={
        "title": "real user issue",
        "message": "please keep this open",
    })

    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cleanup = client.post("/api/v1/admin/feedback/cleanup-live-acceptance", headers=headers)
    feedback = client.get("/api/v1/admin/feedback", headers=headers)

    assert cleanup.status_code == 200
    assert cleanup.json()["closed_count"] == 1
    reports = {item["title"]: item["status"] for item in feedback.json()}
    assert reports["live acceptance 123"] == "closed"
    assert reports["real user issue"] == "new"


def test_admin_can_preview_and_cleanup_expired_cloud_files(client, tmp_path, monkeypatch):
    import os
    import time
    from app.core.config import settings

    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(settings, "CLOUD_FILE_UPLOAD_TTL_SECONDS", 10)
    monkeypatch.setattr(settings, "CLOUD_FILE_RESULT_TTL_SECONDS", 10)
    monkeypatch.setattr(settings, "CLOUD_FILE_DOWNLOAD_TTL_SECONDS", 10)

    expired_upload = tmp_path / "file_old_abc"
    expired_result = tmp_path / "merge_old_abc"
    keep_unknown = tmp_path / "manual_docs"
    fresh_upload = tmp_path / "file_fresh_abc"
    for directory in (expired_upload, expired_result, keep_unknown, fresh_upload):
        directory.mkdir()
        (directory / "sample.pdf").write_bytes(b"%PDF-1.4")

    old_time = time.time() - 60
    for directory in (expired_upload, expired_result, keep_unknown):
        os.utime(directory, (old_time, old_time))

    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    summary = client.get("/api/v1/admin/maintenance", headers=headers)
    cleanup = client.post("/api/v1/admin/files/cleanup-expired", headers=headers)

    assert summary.status_code == 200
    assert summary.json()["file_retention"]["removable_count"] == 2
    assert cleanup.status_code == 200
    assert cleanup.json()["removed_count"] == 2
    assert not expired_upload.exists()
    assert not expired_result.exists()
    assert keep_unknown.exists()
    assert fresh_upload.exists()


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
        @app.post(route_path)
        async def _test_observable_error():
            raise RuntimeError("observable test failure")

    _register(client)
    _promote_to_admin(client)
    token = _login(client).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(app, raise_server_exceptions=False) as safe_client:
        failed = safe_client.post(
            f"{route_path}?debug=visible-query",
            json={"secret_document_text": "do-not-copy-this-body"},
            headers={"x-request-id": "req_admin_diagnostics_test"},
        )
        assert failed.status_code == 500

    errors = client.get("/api/v1/admin/errors", headers=headers)
    assert errors.status_code == 200
    assert errors.json()[0]["path"] == route_path
    assert errors.json()[0]["method"] == "POST"
    assert errors.json()[0]["request_id"] == "req_admin_diagnostics_test"
    assert errors.json()[0]["status_code"] == 500
    assert "do-not-copy-this-body" not in str(errors.json()[0])

    diagnostics = client.get("/api/v1/admin/diagnostics", headers=headers)
    assert diagnostics.status_code == 200
    body = diagnostics.json()
    assert body["api_error_count"] >= 1
    assert body["recent_errors"][0]["path"] == route_path
    assert "diagnostic_summary" in body
    assert "PDF-Flow diagnostic packet" in body["diagnostic_summary"]
    assert "req_admin_diagnostics_test" in body["diagnostic_summary"]
    assert "POST /api/v1/test-observable-error" in body["diagnostic_summary"]
    assert "do-not-copy-this-body" not in body["diagnostic_summary"]
    assert "request bodies and document contents are not included" in body["diagnostic_summary"]
