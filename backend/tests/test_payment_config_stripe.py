"""Admin-managed Stripe payment config tests."""


def _register(client, email, password="SecurePass123!"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Stripe Config User"},
    )


def _login(client, email, password="SecurePass123!"):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


def _make_admin(client, email="stripe-admin@example.com"):
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


def _make_user_headers(client, email="stripe-buyer@example.com"):
    _register(client, email=email)
    token = _login(client, email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _stripe_payload(secret_key="sk_test_config_1234", webhook_secret="whsec_config_5678"):
    return {
        "enabled": True,
        "public_config": {
            "price_id_monthly": "price_db_monthly",
            "price_id_yearly": "price_db_yearly",
        },
        "secrets": {
            "secret_key": secret_key,
            "webhook_secret": webhook_secret,
        },
    }


class _FakeStripeSession:
    calls = []

    @staticmethod
    def create(**kwargs):
        _FakeStripeSession.calls.append(kwargs)
        return type(
            "StripeSession",
            (),
            {"id": "cs_db_stripe_001", "url": "https://checkout.stripe.test/session/cs_db_stripe_001"},
        )()


def test_admin_can_save_stripe_config_without_secret_leak(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.models.user import AdminAuditLog, PaymentProviderConfig

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    headers = _make_admin(client)
    payload = _stripe_payload("sk_live_do_not_echo_1234", "whsec_do_not_echo_5678")

    response = client.put(
        "/api/v1/admin/payment-configs/stripe",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 200
    body_text = response.text
    body = response.json()
    assert "sk_live_do_not_echo_1234" not in body_text
    assert "whsec_do_not_echo_5678" not in body_text
    assert body["enabled"] is True
    assert body["configured"] is True
    assert body["public_config"]["price_id_monthly"] == "price_db_monthly"
    assert body["secret_fields"]["secret_key"] == {"configured": True, "tail": "1234"}
    assert body["secret_fields"]["webhook_secret"] == {"configured": True, "tail": "5678"}
    assert body["metadata"]["provider_key"] == "stripe"
    assert [field["key"] for field in body["metadata"]["fields"]["public"]] == [
        "price_id_monthly",
        "price_id_yearly",
    ]
    assert [field["key"] for field in body["metadata"]["fields"]["secret"]] == [
        "secret_key",
        "webhook_secret",
    ]
    assert body["readiness"]["status"] == "ready"
    assert body["readiness"]["validation_checks"] == ["required_fields", "stripe_checkout_schema"]

    db = next(client.app.dependency_overrides[get_db]())
    try:
        row = db.query(PaymentProviderConfig).filter(
            PaymentProviderConfig.provider_key == "stripe"
        ).first()
        assert row is not None
        assert "sk_live_do_not_echo_1234" not in (row.encrypted_secret_json or "")
        assert "whsec_do_not_echo_5678" not in (row.encrypted_secret_json or "")

        audit = db.query(AdminAuditLog).filter(
            AdminAuditLog.action == "payment_config.update",
            AdminAuditLog.target_key == "stripe",
        ).first()
        assert audit is not None
        assert "sk_live_do_not_echo_1234" not in (audit.detail or "")
        assert "whsec_do_not_echo_5678" not in (audit.detail or "")
        assert "secret_key" in (audit.detail or "")
        assert "webhook_secret" in (audit.detail or "")
    finally:
        db.close()


def test_empty_stripe_secret_keeps_existing_encrypted_secret(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.models.user import PaymentProviderConfig

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    headers = _make_admin(client, email="stripe-admin-keep@example.com")

    first = client.put(
        "/api/v1/admin/payment-configs/stripe",
        headers=headers,
        json=_stripe_payload("sk_first_9999", "whsec_first_8888"),
    )
    assert first.status_code == 200

    db = next(client.app.dependency_overrides[get_db]())
    try:
        before = db.query(PaymentProviderConfig).filter(
            PaymentProviderConfig.provider_key == "stripe"
        ).first().encrypted_secret_json
    finally:
        db.close()

    payload = _stripe_payload("", "")
    payload["public_config"]["price_id_monthly"] = "price_db_monthly_updated"
    payload["secrets"] = {}
    second = client.put(
        "/api/v1/admin/payment-configs/stripe",
        headers=headers,
        json=payload,
    )

    assert second.status_code == 200
    assert second.json()["secret_fields"]["secret_key"]["tail"] == "9999"
    assert second.json()["secret_fields"]["webhook_secret"]["tail"] == "8888"

    db = next(client.app.dependency_overrides[get_db]())
    try:
        after = db.query(PaymentProviderConfig).filter(
            PaymentProviderConfig.provider_key == "stripe"
        ).first().encrypted_secret_json
        assert after == before
    finally:
        db.close()


def test_validate_stripe_is_local_only(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    headers = _make_admin(client, email="stripe-admin-validate@example.com")

    response = client.post(
        "/api/v1/admin/payment-configs/stripe/validate",
        headers=headers,
        json=_stripe_payload("sk_validate", "whsec_validate"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["checks"] == ["required_fields", "stripe_checkout_schema"]
    assert body["signature_preview_tail"] is None


def test_admin_payment_configs_are_registry_driven_for_visible_providers(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    headers = _make_admin(client, email="providers-registry-admin@example.com")

    response = client.get("/api/v1/admin/payment-configs", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert [item["provider_key"] for item in body] == ["stripe", "paypal", "gmpay"]

    paypal = next(item for item in body if item["provider_key"] == "paypal")
    assert paypal["metadata"]["fields"]["public"][0]["key"] == "api_base_url"
    assert paypal["metadata"]["fields"]["secret"][0]["key"] == "client_secret"
    assert paypal["metadata"]["fields"]["secret"][0]["secret"] is True
    assert "client_secret" in paypal["readiness"]["missing_config_keys"]

    gmpay = next(item for item in body if item["provider_key"] == "gmpay")
    assert [field["key"] for field in gmpay["metadata"]["fields"]["public"]] == [
        "api_base_url",
        "pid",
        "currency",
        "token",
        "network",
        "monthly_amount_cents",
        "yearly_amount_cents",
        "order_ttl_minutes",
        "return_url",
    ]
    assert gmpay["metadata"]["validation_checks"] == [
        "required_fields",
        "local_signature_generation",
    ]


def test_stripe_checkout_uses_db_config_and_creates_pending_order(client, monkeypatch):
    import stripe

    from app.core.config import settings
    from app.core.database import get_db
    from app.models.user import PaymentOrder

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "")
    monkeypatch.setattr(stripe.checkout, "Session", _FakeStripeSession)
    _FakeStripeSession.calls = []

    admin_headers = _make_admin(client, email="stripe-admin-checkout@example.com")
    saved = client.put(
        "/api/v1/admin/payment-configs/stripe",
        headers=admin_headers,
        json=_stripe_payload("sk_db_checkout", "whsec_db_checkout"),
    )
    assert saved.status_code == 200

    providers = client.get("/api/v1/payment/providers").json()["providers"]
    stripe_provider = next(item for item in providers if item["key"] == "stripe")
    assert stripe_provider["enabled"] is True
    assert stripe_provider["supports_subscription"] is True

    user_headers = _make_user_headers(client)
    checkout = client.post(
        "/api/v1/payment/create-checkout-session",
        headers=user_headers,
        json={
            "provider": "stripe",
            "plan": "monthly",
            "success_url": "http://localhost:5173/payment/success",
            "cancel_url": "http://localhost:5173/payment/cancel",
        },
    )

    assert checkout.status_code == 200
    body = checkout.json()
    assert body["provider"] == "stripe"
    assert body["checkout_url"] == "https://checkout.stripe.test/session/cs_db_stripe_001"
    assert _FakeStripeSession.calls[0]["line_items"] == [{"price": "price_db_monthly", "quantity": 1}]
    assert stripe.api_key == "sk_db_checkout"

    db = next(client.app.dependency_overrides[get_db]())
    try:
        order = db.query(PaymentOrder).filter(
            PaymentOrder.merchant_order_id == body["merchant_order_id"]
        ).first()
        assert order is not None
        assert order.status == "pending"
        assert order.provider == "stripe"
        assert order.provider_order_id == "cs_db_stripe_001"
        assert order.amount_cents == 990
        assert order.currency == "USD"
    finally:
        db.close()
