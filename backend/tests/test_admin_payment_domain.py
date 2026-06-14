"""Admin payment operations domain tests."""

from datetime import datetime, timedelta


def _register(client, email="admin-payment-domain@example.com", password="SecurePass123!"):
    return client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Admin Payment Domain",
    })


def test_payment_operations_summary_reports_provider_readiness_and_safe_packets(client, monkeypatch):
    from app.core.config import settings
    from app.core.database import get_db
    from app.domains.admin.payment_ops import get_payment_operations_summary
    from app.models.user import PaymentEvent, PaymentOrder, User

    monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "stripe,epusdt,wechat")
    monkeypatch.setattr(settings, "PAYMENT_GATEWAY_CONFIGS_RAW", "{}")
    monkeypatch.setattr(settings, "BACKEND_PUBLIC_URL", "https://api.pdf-flow.test")
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://app.pdf-flow.test")
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_admin_domain")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_admin_domain")
    monkeypatch.setattr(settings, "STRIPE_PRICE_ID_MONTHLY", "price_monthly_domain")
    monkeypatch.setattr(settings, "STRIPE_PRICE_ID_YEARLY", "price_yearly_domain")
    monkeypatch.setattr(settings, "WECHAT_PAY_APP_ID", "wx_domain")
    monkeypatch.setattr(settings, "WECHAT_PAY_MCH_ID", "mch_domain")
    monkeypatch.setattr(settings, "WECHAT_PAY_SERIAL_NO", "serial_domain")
    monkeypatch.setattr(settings, "WECHAT_PAY_PRIVATE_KEY", "private_key_domain")
    monkeypatch.setattr(settings, "WECHAT_PAY_API_V3_KEY", "api_v3_domain")
    monkeypatch.setattr(settings, "WECHAT_PAY_PLATFORM_CERT", "platform_cert_domain")

    _register(client, email="paying-domain@example.com")
    db = next(client.app.dependency_overrides[get_db]())
    try:
        payer = db.query(User).filter(User.email == "paying-domain@example.com").first()
        db.add_all([
            PaymentOrder(
                user_id=payer.id,
                provider="stripe",
                merchant_order_id="pf_domain_paid",
                provider_order_id="cs_domain_paid",
                plan="monthly",
                amount_cents=990,
                currency="USD",
                status="paid",
                checkout_url="https://checkout.stripe.local/secret-session",
                paid_at=datetime.utcnow(),
            ),
            PaymentOrder(
                user_id=payer.id,
                provider="epusdt",
                merchant_order_id="pf_domain_pending",
                provider_order_id="usdt_domain_pending",
                plan="yearly",
                amount_cents=7900,
                currency="USD",
                status="pending",
                qr_code_url="tron:private-domain-address",
                expires_at=datetime.utcnow() - timedelta(minutes=5),
            ),
            PaymentOrder(
                user_id=payer.id,
                provider="wechat",
                merchant_order_id="pf_domain_review",
                provider_order_id="wx_domain_review",
                plan="monthly",
                amount_cents=990,
                currency="CNY",
                status="currency_mismatch",
            ),
        ])
        db.commit()
        paid_order = db.query(PaymentOrder).filter(
            PaymentOrder.merchant_order_id == "pf_domain_paid"
        ).first()
        db.add(PaymentEvent(
            order_id=paid_order.id,
            provider="stripe",
            provider_event_id="evt_domain_paid",
            merchant_order_id="pf_domain_paid",
            provider_order_id="cs_domain_paid",
            event_type="paid",
            processing_status="applied",
            amount_cents=990,
            currency="USD",
            raw_summary='{"type":"checkout.session.completed"}',
        ))
        db.commit()

        summary = get_payment_operations_summary(db, provider="epusdt", status_filter="pending")
    finally:
        db.close()

    assert summary["total_orders"] == 3
    assert summary["pending_orders"] == 1
    assert summary["paid_orders"] == 1
    assert summary["currency_mismatch_orders"] == 1
    assert summary["expired_pending_orders"] == 1
    assert summary["paid_amount_cents"] == 990
    assert summary["currency_breakdown"] == {"USD": 990}
    assert [item["provider"] for item in summary["recent_orders"]] == ["epusdt"]

    stripe = next(provider for provider in summary["providers"] if provider["key"] == "stripe")

    assert [provider["key"] for provider in summary["providers"]] == ["stripe", "paypal", "gmpay"]

    assert stripe["acceptance_status"] == "accepted"
    assert stripe["webhook_url"] == "https://api.pdf-flow.test/api/v1/payment/webhooks/stripe"
    assert stripe["latest_paid_event_at"] is not None

    assert "checkout.stripe.local" not in summary["reconciliation_summary"]
    assert "tron:private-domain-address" not in summary["reconciliation_summary"]
    assert "checkout.stripe.local" not in summary["integration_evidence_packet"]
    assert "tron:private-domain-address" not in summary["integration_evidence_packet"]
    assert "provider_dashboard_event_url=" in summary["integration_evidence_packet"]
    assert "evt_domain_paid" in summary["integration_evidence_packet"]

