"""Admin-managed payment config and GM Pay Phase 1 tests."""

import json


def _register(client, email, password="SecurePass123!"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Payment Config User"},
    )


def _login(client, email, password="SecurePass123!"):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


def _make_admin(client, email="payment-admin@example.com"):
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


def _make_user_headers(client, email="gmpay-buyer@example.com"):
    _register(client, email=email)
    token = _login(client, email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _gmpay_payload(secret_key="gm-secret-key"):
    return {
        "enabled": True,
        "public_config": {
            "api_base_url": "https://gmpay.example",
            "pid": "gm-pid",
            "currency": "cny",
            "token": "usdt",
            "network": "tron",
            "monthly_amount_cents": 1234,
            "yearly_amount_cents": 9900,
            "order_ttl_minutes": 20,
            "return_url": "",
        },
        "secrets": {"secret_key": secret_key},
    }


class _FakeGMPayResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class _FakeGMPayClient:
    calls = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _FakeGMPayResponse({
            "data": {
                "trade_id": "GM_TRADE_001",
                "payment_url": "https://gmpay.example/cashier/GM_TRADE_001",
            }
        })


def test_admin_can_save_gmpay_config_without_secret_leak(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.models.user import AdminAuditLog, PaymentProviderConfig

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    headers = _make_admin(client)
    secret = "gm-super-secret-1234"

    response = client.put(
        "/api/v1/admin/payment-configs/gmpay",
        headers=headers,
        json=_gmpay_payload(secret),
    )

    assert response.status_code == 200
    body_text = response.text
    body = response.json()
    assert secret not in body_text
    assert body["enabled"] is True
    assert body["configured"] is True
    assert body["secret_fields"]["secret_key"] == {"configured": True, "tail": "1234"}

    db = next(client.app.dependency_overrides[get_db]())
    try:
        row = db.query(PaymentProviderConfig).filter(
            PaymentProviderConfig.provider_key == "gmpay"
        ).first()
        assert row is not None
        assert secret not in (row.encrypted_secret_json or "")
        assert "1234" in (row.secret_fingerprint_json or "")

        audit = db.query(AdminAuditLog).filter(
            AdminAuditLog.action == "payment_config.update",
            AdminAuditLog.target_key == "gmpay",
        ).first()
        assert audit is not None
        assert secret not in (audit.detail or "")
        assert "secret_key" in (audit.detail or "")
    finally:
        db.close()


def test_empty_secret_keeps_existing_encrypted_secret(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.models.user import PaymentProviderConfig

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    headers = _make_admin(client, email="payment-admin-keep@example.com")

    first = client.put(
        "/api/v1/admin/payment-configs/gmpay",
        headers=headers,
        json=_gmpay_payload("first-secret-9999"),
    )
    assert first.status_code == 200
    db = next(client.app.dependency_overrides[get_db]())
    try:
        before = db.query(PaymentProviderConfig).filter(
            PaymentProviderConfig.provider_key == "gmpay"
        ).first().encrypted_secret_json
    finally:
        db.close()

    payload = _gmpay_payload("")
    payload["public_config"]["pid"] = "gm-pid-updated"
    payload["secrets"] = {}
    second = client.put(
        "/api/v1/admin/payment-configs/gmpay",
        headers=headers,
        json=payload,
    )

    assert second.status_code == 200
    assert second.json()["secret_fields"]["secret_key"]["tail"] == "9999"
    db = next(client.app.dependency_overrides[get_db]())
    try:
        after = db.query(PaymentProviderConfig).filter(
            PaymentProviderConfig.provider_key == "gmpay"
        ).first().encrypted_secret_json
        assert after == before
    finally:
        db.close()


def test_validate_gmpay_is_local_only(client, monkeypatch):
    from app.core.config import settings
    from app.domains.payment.providers import GMPayPaymentProvider

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    monkeypatch.setattr(GMPayPaymentProvider, "http_client_factory", _FakeGMPayClient)
    _FakeGMPayClient.calls = []
    headers = _make_admin(client, email="payment-admin-validate@example.com")

    response = client.post(
        "/api/v1/admin/payment-configs/gmpay/validate",
        headers=headers,
        json=_gmpay_payload("validate-secret"),
    )

    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["signature_preview_tail"]
    assert _FakeGMPayClient.calls == []


def test_gmpay_checkout_uses_db_config_and_creates_pending_order(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.domains.payment.providers import GMPayPaymentProvider, build_gmpay_signature
    from app.models.user import PaymentOrder

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "")
    monkeypatch.setattr(settings, "BACKEND_PUBLIC_URL", "https://api.pdf-flow.test")
    monkeypatch.setattr(GMPayPaymentProvider, "http_client_factory", _FakeGMPayClient)
    _FakeGMPayClient.calls = []

    admin_headers = _make_admin(client, email="payment-admin-checkout@example.com")
    saved = client.put(
        "/api/v1/admin/payment-configs/gmpay",
        headers=admin_headers,
        json=_gmpay_payload("checkout-secret"),
    )
    assert saved.status_code == 200

    providers = client.get("/api/v1/payment/providers").json()["providers"]
    gmpay = next(item for item in providers if item["key"] == "gmpay")
    assert gmpay["enabled"] is True

    user_headers = _make_user_headers(client)
    checkout = client.post(
        "/api/v1/payment/create-checkout-session",
        headers=user_headers,
        json={
            "provider": "gmpay",
            "plan": "monthly",
            "success_url": "http://localhost:5173/payment/success",
            "cancel_url": "http://localhost:5173/payment/cancel",
        },
    )

    assert checkout.status_code == 200
    body = checkout.json()
    assert body["provider"] == "gmpay"
    assert body["checkout_url"] == "https://gmpay.example/cashier/GM_TRADE_001"
    assert body["qr_code_url"] == "https://gmpay.example/cashier/GM_TRADE_001"

    call_url, call_kwargs = _FakeGMPayClient.calls[0]
    assert call_url == "https://gmpay.example/payments/gmpay/v1/order/create-transaction"
    payload = call_kwargs["json"]
    assert payload["pid"] == "gm-pid"
    assert payload["amount"] == "12.34"
    assert payload["notify_url"] == "https://api.pdf-flow.test/api/v1/payment/webhooks/gmpay"
    assert payload["signature"] == build_gmpay_signature(payload, "checkout-secret")

    db = next(client.app.dependency_overrides[get_db]())
    try:
        order = db.query(PaymentOrder).filter(
            PaymentOrder.merchant_order_id == body["merchant_order_id"]
        ).first()
        assert order is not None
        assert order.status == "pending"
        assert order.amount_cents == 1234
        assert order.currency == "CNY"
        assert order.provider_order_id == "GM_TRADE_001"
    finally:
        db.close()


def test_gmpay_webhook_skeleton_does_not_grant_pro(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.domains.payment.providers import GMPayPaymentProvider
    from app.models.user import PaymentEvent, PaymentOrder, User, UserRole

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    monkeypatch.setattr(GMPayPaymentProvider, "http_client_factory", _FakeGMPayClient)
    _FakeGMPayClient.calls = []

    admin_headers = _make_admin(client, email="payment-admin-webhook@example.com")
    assert client.put(
        "/api/v1/admin/payment-configs/gmpay",
        headers=admin_headers,
        json=_gmpay_payload("webhook-secret"),
    ).status_code == 200

    user_headers = _make_user_headers(client, email="gmpay-webhook-buyer@example.com")
    checkout = client.post(
        "/api/v1/payment/create-checkout-session",
        headers=user_headers,
        json={
            "provider": "gmpay",
            "plan": "monthly",
            "success_url": "http://localhost:5173/payment/success",
            "cancel_url": "http://localhost:5173/payment/cancel",
        },
    )
    merchant_order_id = checkout.json()["merchant_order_id"]

    webhook = client.post(
        "/api/v1/payment/webhooks/gmpay",
        content=json.dumps({
            "order_id": merchant_order_id,
            "trade_id": "GM_TRADE_001",
            "status": "paid",
            "amount": "12.34",
            "currency": "cny",
        }).encode("utf-8"),
        headers={"content-type": "application/json"},
    )

    assert webhook.status_code == 202
    db = next(client.app.dependency_overrides[get_db]())
    try:
        order = db.query(PaymentOrder).filter(
            PaymentOrder.merchant_order_id == merchant_order_id
        ).first()
        user = db.query(User).filter(User.email == "gmpay-webhook-buyer@example.com").first()
        event = db.query(PaymentEvent).filter(
            PaymentEvent.provider == "gmpay",
            PaymentEvent.merchant_order_id == merchant_order_id,
        ).first()
        assert order.status == "pending"
        assert user.role == UserRole.FREE
        assert event is not None
        assert event.processing_status == "ignored"
        assert event.event_type == "accepted"
    finally:
        db.close()
