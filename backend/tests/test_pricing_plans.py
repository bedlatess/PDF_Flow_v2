"""Admin-managed plans and pricing catalog tests."""


def _register(client, email, password="SecurePass123!"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Pricing Admin"},
    )


def _login(client, email, password="SecurePass123!"):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


def _make_admin(client, email="plans-admin@example.com"):
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


def _make_user_headers(client, email="plans-buyer@example.com"):
    _register(client, email=email)
    token = _login(client, email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _stripe_payload():
    return {
        "enabled": True,
        "public_config": {
            "price_id_monthly": "price_provider_monthly",
            "price_id_yearly": "price_provider_yearly",
        },
        "secrets": {
            "secret_key": "sk_pricing_config",
            "webhook_secret": "whsec_pricing_config",
        },
    }


def _plan_payload(plan):
    payload = dict(plan)
    payload.pop("id", None)
    payload.pop("updated_at", None)
    return payload


class _FakeStripeSession:
    calls = []

    @staticmethod
    def create(**kwargs):
        _FakeStripeSession.calls.append(kwargs)
        return type(
            "StripeSession",
            (),
            {"id": "cs_pricing_plan_001", "url": "https://checkout.stripe.test/pricing"},
        )()


def test_public_pricing_empty_catalog_uses_frontend_fallback(client):
    response = client.get("/api/v1/pricing/plans")

    assert response.status_code == 200
    assert response.json() == {"source": "fallback", "plans": []}


def test_admin_can_seed_update_pricing_plan_and_audit_changed_fields(client):
    from app.core.database import get_db
    from app.models.user import AdminAuditLog

    headers = _make_admin(client)

    listed = client.get("/api/v1/admin/pricing-plans", headers=headers)
    assert listed.status_code == 200
    plans = listed.json()
    assert [plan["plan_key"] for plan in plans] == [
        "free",
        "pro_monthly",
        "pro_yearly",
        "enterprise",
    ]

    monthly = next(plan for plan in plans if plan["plan_key"] == "pro_monthly")
    payload = _plan_payload(monthly)
    payload["display_name"] = "Pro Monthly Managed"
    payload["display_price"] = "$12.34"
    payload["price_amount_cents"] = 1234
    payload["provider_mappings"]["stripe"]["price_id"] = "price_managed_monthly"
    payload["provider_mappings"]["paypal"]["plan_id"] = "P-MANAGED"
    payload["provider_mappings"]["paypal"]["product_id"] = "PROD-MANAGED"
    payload["provider_mappings"]["gmpay"]["amount_cents"] = 1234
    payload["provider_mappings"]["gmpay"]["currency"] = "CNY"
    payload["provider_mappings"]["gmpay"]["token"] = "usdt"
    payload["provider_mappings"]["gmpay"]["network"] = "tron"

    updated = client.put(
        "/api/v1/admin/pricing-plans/pro_monthly",
        headers=headers,
        json=payload,
    )

    assert updated.status_code == 200
    body = updated.json()
    assert body["display_name"] == "Pro Monthly Managed"
    assert body["provider_mappings"]["stripe"]["price_id"] == "price_managed_monthly"

    db = next(client.app.dependency_overrides[get_db]())
    try:
        audit = db.query(AdminAuditLog).filter(
            AdminAuditLog.target_type == "pricing_plan",
            AdminAuditLog.target_key == "pro_monthly",
        ).first()
        assert audit is not None
        assert "changed_fields=" in (audit.detail or "")
        assert "provider_mappings" in (audit.detail or "")
    finally:
        db.close()


def test_checkout_uses_db_first_pricing_mapping_with_provider_fallback(client, monkeypatch):
    import stripe

    from app.core.config import settings
    from app.core.database import get_db
    from app.models.user import PaymentOrder

    monkeypatch.setattr(settings, "PAYMENT_CONFIG_ENCRYPTION_KEY", "unit-test-payment-config-key")
    monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "")
    monkeypatch.setattr(stripe.checkout, "Session", _FakeStripeSession)
    _FakeStripeSession.calls = []

    admin_headers = _make_admin(client, email="plans-checkout-admin@example.com")
    saved = client.put(
        "/api/v1/admin/payment-configs/stripe",
        headers=admin_headers,
        json=_stripe_payload(),
    )
    assert saved.status_code == 200

    plans = client.get("/api/v1/admin/pricing-plans", headers=admin_headers).json()
    monthly = next(plan for plan in plans if plan["plan_key"] == "pro_monthly")
    payload = _plan_payload(monthly)
    payload["price_amount_cents"] = 1234
    payload["currency"] = "USD"
    payload["provider_mappings"]["stripe"]["price_id"] = "price_db_first_monthly"
    updated = client.put(
        "/api/v1/admin/pricing-plans/pro_monthly",
        headers=admin_headers,
        json=payload,
    )
    assert updated.status_code == 200

    user_headers = _make_user_headers(client)
    checkout = client.post(
        "/api/v1/payment/create-checkout-session",
        headers=user_headers,
        json={
            "provider": "stripe",
            "plan": "pro_monthly",
            "success_url": "http://localhost:5173/payment/success",
            "cancel_url": "http://localhost:5173/payment/cancel",
        },
    )

    assert checkout.status_code == 200
    assert _FakeStripeSession.calls[0]["line_items"] == [
        {"price": "price_db_first_monthly", "quantity": 1}
    ]

    db = next(client.app.dependency_overrides[get_db]())
    try:
        order = db.query(PaymentOrder).filter(
            PaymentOrder.merchant_order_id == checkout.json()["merchant_order_id"]
        ).first()
        assert order is not None
        assert order.plan == "pro_monthly"
        assert order.amount_cents == 1234
        assert order.currency == "USD"
    finally:
        db.close()
