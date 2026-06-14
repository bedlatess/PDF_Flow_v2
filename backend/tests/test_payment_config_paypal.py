"""Admin-managed PayPal payment config tests."""


def _register(client, email, password="SecurePass123!"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "PayPal Config User"},
    )


def _login(client, email, password="SecurePass123!"):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


def _make_admin(client, email="paypal-admin@example.com"):
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


def _make_user_headers(client, email="paypal-buyer@example.com"):
    _register(client, email=email)
    token = _login(client, email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _paypal_payload(client_secret="paypal-secret-1234"):
    return {
        "enabled": True,
        "public_config": {
            "api_base_url": "https://api-m.sandbox.paypal.com",
            "client_id": "paypal-client-id",
            "webhook_id": "paypal-webhook-id",
        },
        "secrets": {"client_secret": client_secret},
    }


class _FakePayPalResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakePayPalClient:
    calls = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if url.endswith("/v1/oauth2/token"):
            return _FakePayPalResponse({"access_token": "paypal_access_token"})

        if url.endswith("/v2/checkout/orders"):
            payload = kwargs["json"]
            merchant_order_id = payload["purchase_units"][0]["custom_id"]
            return _FakePayPalResponse({
                "id": "PAYPAL_DB_ORDER_001",
                "status": "CREATED",
                "links": [
                    {
                        "rel": "approve",
                        "href": "https://www.paypal.com/checkoutnow?token=PAYPAL_DB_ORDER_001",
                    },
                ],
                "purchase_units": [
                    {
                        "custom_id": merchant_order_id,
                        "invoice_id": merchant_order_id,
                        "amount": {"currency_code": "USD", "value": "9.90"},
                    }
                ],
            })

        return _FakePayPalResponse({"error": "unexpected url"}, status_code=404)


def test_admin_can_save_paypal_config_without_secret_leak(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.models.user import AdminAuditLog, PaymentProviderConfig

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    headers = _make_admin(client)
    secret = "paypal-client-secret-1234"

    response = client.put(
        "/api/v1/admin/payment-configs/paypal",
        headers=headers,
        json=_paypal_payload(secret),
    )

    assert response.status_code == 200
    body_text = response.text
    body = response.json()
    assert secret not in body_text
    assert body["enabled"] is True
    assert body["configured"] is True
    assert body["public_config"]["client_id"] == "paypal-client-id"
    assert body["secret_fields"]["client_secret"] == {"configured": True, "tail": "1234"}

    db = next(client.app.dependency_overrides[get_db]())
    try:
        row = db.query(PaymentProviderConfig).filter(
            PaymentProviderConfig.provider_key == "paypal"
        ).first()
        assert row is not None
        assert secret not in (row.encrypted_secret_json or "")

        audit = db.query(AdminAuditLog).filter(
            AdminAuditLog.action == "payment_config.update",
            AdminAuditLog.target_key == "paypal",
        ).first()
        assert audit is not None
        assert secret not in (audit.detail or "")
        assert "client_secret" in (audit.detail or "")
    finally:
        db.close()


def test_empty_paypal_secret_keeps_existing_encrypted_secret(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.models.user import PaymentProviderConfig

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    headers = _make_admin(client, email="paypal-admin-keep@example.com")

    first = client.put(
        "/api/v1/admin/payment-configs/paypal",
        headers=headers,
        json=_paypal_payload("paypal-first-secret-9999"),
    )
    assert first.status_code == 200
    db = next(client.app.dependency_overrides[get_db]())
    try:
        before = db.query(PaymentProviderConfig).filter(
            PaymentProviderConfig.provider_key == "paypal"
        ).first().encrypted_secret_json
    finally:
        db.close()

    payload = _paypal_payload("")
    payload["public_config"]["client_id"] = "paypal-client-id-updated"
    payload["secrets"] = {}
    second = client.put(
        "/api/v1/admin/payment-configs/paypal",
        headers=headers,
        json=payload,
    )

    assert second.status_code == 200
    assert second.json()["secret_fields"]["client_secret"]["tail"] == "9999"
    db = next(client.app.dependency_overrides[get_db]())
    try:
        after = db.query(PaymentProviderConfig).filter(
            PaymentProviderConfig.provider_key == "paypal"
        ).first().encrypted_secret_json
        assert after == before
    finally:
        db.close()


def test_validate_paypal_is_local_only(client, monkeypatch):
    from app.core.config import settings
    from app.domains.payment.providers import PayPalPaymentProvider

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    monkeypatch.setattr(PayPalPaymentProvider, "http_client_factory", _FakePayPalClient)
    _FakePayPalClient.calls = []
    headers = _make_admin(client, email="paypal-admin-validate@example.com")

    response = client.post(
        "/api/v1/admin/payment-configs/paypal/validate",
        headers=headers,
        json=_paypal_payload("paypal-validate-secret"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["checks"] == ["required_fields", "paypal_checkout_schema"]
    assert _FakePayPalClient.calls == []


def test_paypal_checkout_uses_db_config_and_creates_pending_order(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.domains.payment.providers import PayPalPaymentProvider
    from app.models.user import PaymentOrder

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "")
    monkeypatch.setattr(PayPalPaymentProvider, "http_client_factory", _FakePayPalClient)
    _FakePayPalClient.calls = []

    admin_headers = _make_admin(client, email="paypal-admin-checkout@example.com")
    saved = client.put(
        "/api/v1/admin/payment-configs/paypal",
        headers=admin_headers,
        json=_paypal_payload("paypal-db-checkout-secret"),
    )
    assert saved.status_code == 200

    providers = client.get("/api/v1/payment/providers").json()["providers"]
    paypal = next(item for item in providers if item["key"] == "paypal")
    assert paypal["enabled"] is True

    user_headers = _make_user_headers(client)
    checkout = client.post(
        "/api/v1/payment/create-checkout-session",
        headers=user_headers,
        json={
            "provider": "paypal",
            "plan": "monthly",
            "success_url": "http://localhost:5173/payment/success",
            "cancel_url": "http://localhost:5173/payment/cancel",
        },
    )

    assert checkout.status_code == 200
    body = checkout.json()
    assert body["provider"] == "paypal"
    assert body["checkout_url"] == "https://www.paypal.com/checkoutnow?token=PAYPAL_DB_ORDER_001"

    token_call = [call for call in _FakePayPalClient.calls if call[0].endswith("/v1/oauth2/token")][0]
    assert token_call[1]["auth"] == ("paypal-client-id", "paypal-db-checkout-secret")
    order_call = [call for call in _FakePayPalClient.calls if call[0].endswith("/v2/checkout/orders")][0]
    assert order_call[1]["json"]["purchase_units"][0]["amount"]["value"] == "9.90"

    db = next(client.app.dependency_overrides[get_db]())
    try:
        order = db.query(PaymentOrder).filter(
            PaymentOrder.merchant_order_id == body["merchant_order_id"]
        ).first()
        assert order is not None
        assert order.status == "pending"
        assert order.provider == "paypal"
        assert order.provider_order_id == "PAYPAL_DB_ORDER_001"
        assert order.amount_cents == 990
        assert order.currency == "USD"
    finally:
        db.close()
