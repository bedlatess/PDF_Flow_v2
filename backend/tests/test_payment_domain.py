"""Payment domain tests.

These tests lock the new provider-agnostic payment boundary: checkout may be
started from the frontend, but Pro entitlement only changes after the backend
marks a trusted order as paid.
"""

from datetime import datetime
import json
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _test_key_pair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


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
        self.args = args
        self.kwargs = kwargs

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
                "id": "PAYPAL_ORDER_001",
                "status": "CREATED",
                "links": [
                    {"rel": "self", "href": "https://api-m.sandbox.paypal.com/v2/checkout/orders/PAYPAL_ORDER_001"},
                    {"rel": "approve", "href": "https://www.paypal.com/checkoutnow?token=PAYPAL_ORDER_001"},
                ],
                "purchase_units": [
                    {
                        "custom_id": merchant_order_id,
                        "invoice_id": merchant_order_id,
                        "amount": {"currency_code": "USD", "value": "9.90"},
                    }
                ],
            })

        if url.endswith("/v2/checkout/orders/PAYPAL_ORDER_001/capture"):
            return _FakePayPalResponse({
                "id": "PAYPAL_ORDER_001",
                "status": "COMPLETED",
                "purchase_units": [
                    {
                        "custom_id": _FakePayPalClient.current_merchant_order_id,
                        "invoice_id": _FakePayPalClient.current_merchant_order_id,
                        "payments": {
                            "captures": [
                                {
                                    "id": "PAYPAL_CAPTURE_001",
                                    "status": "COMPLETED",
                                    "amount": {"currency_code": "USD", "value": "9.90"},
                                }
                            ]
                        },
                    }
                ],
            })

        if url.endswith("/v1/notifications/verify-webhook-signature"):
            return _FakePayPalResponse({"verification_status": _FakePayPalClient.verification_status})

        return _FakePayPalResponse({"error": "unexpected url"}, status_code=404)


_FakePayPalClient.current_merchant_order_id = ""
_FakePayPalClient.verification_status = "SUCCESS"


class _FakeWeChatResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeWeChatClient:
    calls = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if url.endswith("/v3/pay/transactions/native"):
            return _FakeWeChatResponse({"code_url": "weixin://wxpay/bizpayurl?pr=test"})
        return _FakeWeChatResponse({"error": "unexpected url"}, status_code=404)


def _register(client, email="payer@example.com", password="SecurePass123!"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Payment User"},
    )


def _login(client, email="payer@example.com", password="SecurePass123!"):
    return client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


def _auth_headers(client, email="payer@example.com"):
    _register(client, email=email)
    token = _login(client, email=email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestPaymentProviders:
    def test_lists_payment_provider_registry(self, client):
        r = client.get("/api/v1/payment/providers")

        assert r.status_code == 200
        providers = r.json()["providers"]
        keys = [item["key"] for item in providers]
        assert keys[:4] == ["stripe", "paypal", "epay", "alipay"]
        assert any(item["key"] == "wechat" for item in providers)
        assert any(item["key"] == "epusdt" for item in providers)
        assert providers[0]["enabled"] is False
        assert not any(item["enabled"] for item in providers)

    def test_stripe_checkout_is_disabled_by_default(self, client):
        headers = _auth_headers(client)

        r = client.post(
            "/api/v1/payment/create-checkout-session",
            headers=headers,
            json={
                "provider": "stripe",
                "plan": "monthly",
                "success_url": "http://localhost:5173/payment/success",
                "cancel_url": "http://localhost:5173/payment/cancel",
            },
        )

        assert r.status_code == 503
        assert r.json()["detail"] == "Stripe payment is not enabled"

    def test_checkout_rejects_disabled_provider(self, client):
        headers = _auth_headers(client)

        r = client.post(
            "/api/v1/payment/create-checkout-session",
            headers=headers,
            json={
                "provider": "paypal",
                "plan": "monthly",
                "success_url": "http://localhost:5173/payment/success",
                "cancel_url": "http://localhost:5173/payment/cancel",
            },
        )

        assert r.status_code == 503
        assert "PayPal" in r.json()["detail"]

    def test_checkout_creates_stub_gateway_order_when_gateway_is_configured(self, client, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "epay")
        monkeypatch.setattr(
            settings,
            "PAYMENT_GATEWAY_CONFIGS_RAW",
            json.dumps({
                "epay": {
                    "merchant_id": "epay-pid",
                    "secret": "epay-secret",
                    "create_url": "https://epay.local/submit.php",
                }
            }),
        )
        headers = _auth_headers(client)

        r = client.post(
            "/api/v1/payment/create-checkout-session",
            headers=headers,
            json={
                "provider": "epay",
                "plan": "yearly",
                "success_url": "http://localhost:5173/payment/success",
                "cancel_url": "http://localhost:5173/payment/cancel",
            },
        )

        assert r.status_code == 200
        body = r.json()
        assert body["provider"] == "epay"
        assert body["merchant_order_id"].startswith("pf_")
        assert body["checkout_url"].startswith("https://epay.local/submit.php?")
        assert "sign=" in body["checkout_url"]

        from app.core.database import get_db
        from app.models.user import PaymentOrder

        db = next(client.app.dependency_overrides[get_db]())
        try:
            order = db.query(PaymentOrder).filter(
                PaymentOrder.merchant_order_id == body["merchant_order_id"]
            ).first()
            assert order is not None
            assert order.status == "pending"
            assert order.amount_cents == 7900
        finally:
            db.close()

    def test_paypal_checkout_creates_real_order_request(self, client, monkeypatch):
        from app.core.config import settings
        from app.domains.payment.providers import PayPalPaymentProvider

        _FakePayPalClient.calls = []
        monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "paypal")
        monkeypatch.setattr(settings, "PAYPAL_CLIENT_ID", "paypal-client")
        monkeypatch.setattr(settings, "PAYPAL_CLIENT_SECRET", "paypal-secret")
        monkeypatch.setattr(settings, "PAYPAL_API_BASE_URL", "https://api-m.sandbox.paypal.com")
        monkeypatch.setattr(PayPalPaymentProvider, "http_client_factory", _FakePayPalClient)
        headers = _auth_headers(client)

        r = client.post(
            "/api/v1/payment/create-checkout-session",
            headers=headers,
            json={
                "provider": "paypal",
                "plan": "monthly",
                "success_url": "http://localhost:5173/payment/success",
                "cancel_url": "http://localhost:5173/payment/cancel",
            },
        )

        assert r.status_code == 200
        body = r.json()
        assert body["provider"] == "paypal"
        assert body["checkout_url"] == "https://www.paypal.com/checkoutnow?token=PAYPAL_ORDER_001"
        assert body["session_id"].startswith("pf_")
        order_call = [call for call in _FakePayPalClient.calls if call[0].endswith("/v2/checkout/orders")][0]
        assert order_call[1]["json"]["intent"] == "CAPTURE"
        assert order_call[1]["json"]["purchase_units"][0]["amount"]["value"] == "9.90"

    def test_paypal_capture_marks_order_paid_and_grants_entitlement(self, client, monkeypatch):
        from app.core.config import settings
        from app.core.database import get_db
        from app.domains.payment.providers import PayPalPaymentProvider
        from app.models.user import User, UserRole

        _FakePayPalClient.calls = []
        monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "paypal")
        monkeypatch.setattr(settings, "PAYPAL_CLIENT_ID", "paypal-client")
        monkeypatch.setattr(settings, "PAYPAL_CLIENT_SECRET", "paypal-secret")
        monkeypatch.setattr(PayPalPaymentProvider, "http_client_factory", _FakePayPalClient)
        headers = _auth_headers(client)
        checkout = client.post(
            "/api/v1/payment/create-checkout-session",
            headers=headers,
            json={
                "provider": "paypal",
                "plan": "monthly",
                "success_url": "http://localhost:5173/payment/success",
                "cancel_url": "http://localhost:5173/payment/cancel",
            },
        )
        assert checkout.status_code == 200
        merchant_order_id = checkout.json()["merchant_order_id"]
        _FakePayPalClient.current_merchant_order_id = merchant_order_id

        capture = client.post(
            f"/api/v1/payment/orders/{merchant_order_id}/capture",
            headers=headers,
        )

        assert capture.status_code == 200
        assert capture.json()["status"] == "paid"
        db = next(client.app.dependency_overrides[get_db]())
        try:
            user = db.query(User).filter(User.email == "payer@example.com").first()
            assert user.role == UserRole.PRO
            assert user.subscription_status == "active"
        finally:
            db.close()

    def test_paypal_webhook_requires_successful_signature_verification(self, client, monkeypatch):
        from app.core.config import settings
        from app.core.database import get_db
        from app.domains.payment.providers import PayPalPaymentProvider
        from app.models.user import PaymentEvent, PaymentOrder, User, UserRole

        monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "paypal")
        monkeypatch.setattr(settings, "PAYPAL_CLIENT_ID", "paypal-client")
        monkeypatch.setattr(settings, "PAYPAL_CLIENT_SECRET", "paypal-secret")
        monkeypatch.setattr(settings, "PAYPAL_WEBHOOK_ID", "webhook-id")
        monkeypatch.setattr(PayPalPaymentProvider, "http_client_factory", _FakePayPalClient)
        headers = _auth_headers(client)
        checkout = client.post(
            "/api/v1/payment/create-checkout-session",
            headers=headers,
            json={
                "provider": "paypal",
                "plan": "monthly",
                "success_url": "http://localhost:5173/payment/success",
                "cancel_url": "http://localhost:5173/payment/cancel",
            },
        )
        merchant_order_id = checkout.json()["merchant_order_id"]
        event = {
            "id": "WH-001",
            "event_type": "PAYMENT.CAPTURE.COMPLETED",
            "resource": {
                "id": "PAYPAL_CAPTURE_001",
                "custom_id": merchant_order_id,
                "invoice_id": merchant_order_id,
                "amount": {"currency_code": "USD", "value": "9.90"},
                "supplementary_data": {"related_ids": {"order_id": "PAYPAL_ORDER_001"}},
            },
        }

        _FakePayPalClient.verification_status = "FAILURE"
        failed = client.post(
            "/api/v1/payment/webhooks/paypal",
            content=json.dumps(event).encode("utf-8"),
            headers={
                "paypal-auth-algo": "SHA256withRSA",
                "paypal-cert-url": "https://api-m.sandbox.paypal.com/certs/test",
                "paypal-transmission-id": "transmission-1",
                "paypal-transmission-sig": "sig",
                "paypal-transmission-time": "2026-06-12T00:00:00Z",
            },
        )
        assert failed.status_code == 400
        assert failed.json()["detail"] == "PayPal webhook verification failed"

        db = next(client.app.dependency_overrides[get_db]())
        try:
            order = db.query(PaymentOrder).filter(PaymentOrder.merchant_order_id == merchant_order_id).first()
            user = db.query(User).filter(User.email == "payer@example.com").first()
            assert order.status == "pending"
            assert user.role == UserRole.FREE
        finally:
            db.close()

        _FakePayPalClient.verification_status = "SUCCESS"
        passed = client.post(
            "/api/v1/payment/webhooks/paypal",
            content=json.dumps(event).encode("utf-8"),
            headers={
                "paypal-auth-algo": "SHA256withRSA",
                "paypal-cert-url": "https://api-m.sandbox.paypal.com/certs/test",
                "paypal-transmission-id": "transmission-2",
                "paypal-transmission-sig": "sig",
                "paypal-transmission-time": "2026-06-12T00:00:00Z",
            },
        )
        assert passed.status_code == 200
        assert passed.json()["merchant_order_id"] == merchant_order_id

        db = next(client.app.dependency_overrides[get_db]())
        try:
            payment_event = db.query(PaymentEvent).filter(
                PaymentEvent.provider == "paypal",
                PaymentEvent.provider_event_id == "WH-001",
            ).first()
            assert payment_event is not None
            assert payment_event.processing_status == "applied"
            assert payment_event.raw_summary == '{"type": "PAYMENT.CAPTURE.COMPLETED"}'
        finally:
            db.close()

    def test_alipay_checkout_and_signed_notification_grant_entitlement(self, client, monkeypatch):
        from urllib.parse import parse_qs, urlparse, urlencode

        from app.core.config import settings
        from app.domains.payment.crypto import canonical_query, rsa2_sign

        private_pem, public_pem = _test_key_pair()
        monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "alipay")
        monkeypatch.setattr(settings, "ALIPAY_APP_ID", "alipay-app")
        monkeypatch.setattr(settings, "ALIPAY_PRIVATE_KEY", private_pem)
        monkeypatch.setattr(settings, "ALIPAY_PUBLIC_KEY", public_pem)
        monkeypatch.setattr(settings, "ALIPAY_GATEWAY_URL", "https://openapi.alipay.test/gateway.do")
        headers = _auth_headers(client)

        checkout = client.post(
            "/api/v1/payment/create-checkout-session",
            headers=headers,
            json={
                "provider": "alipay",
                "plan": "monthly",
                "success_url": "http://localhost:5173/payment/success",
                "cancel_url": "http://localhost:5173/payment/cancel",
            },
        )

        assert checkout.status_code == 200
        body = checkout.json()
        assert body["checkout_url"].startswith("https://openapi.alipay.test/gateway.do?")
        query = parse_qs(urlparse(body["checkout_url"]).query)
        assert query["method"] == ["alipay.trade.page.pay"]
        assert query["sign_type"] == ["RSA2"]
        assert query["notify_url"] == ["http://localhost:8000/api/v1/payment/webhooks/alipay"]
        assert query["return_url"] == [
            f"http://localhost:5173/payment/success?provider=alipay&order_id={body['merchant_order_id']}"
        ]

        notify = {
            "app_id": "alipay-app",
            "trade_no": "ALIPAY_TRADE_001",
            "out_trade_no": body["merchant_order_id"],
            "trade_status": "TRADE_SUCCESS",
            "total_amount": "9.90",
            "seller_id": "seller",
        }
        notify["sign"] = rsa2_sign(private_pem, canonical_query(notify, exclude={"sign", "sign_type"}))
        notify["sign_type"] = "RSA2"
        webhook = client.post(
            "/api/v1/payment/webhooks/alipay",
            content=urlencode(notify).encode("utf-8"),
            headers={"content-type": "application/x-www-form-urlencoded"},
        )

        assert webhook.status_code == 200
        assert webhook.json()["merchant_order_id"] == body["merchant_order_id"]

    def test_wechat_native_checkout_and_encrypted_notification_grant_entitlement(self, client, monkeypatch):
        from app.core.config import settings
        from app.domains.payment.crypto import rsa2_sign
        from app.domains.payment.providers import WeChatPaymentProvider

        merchant_private, _merchant_public = _test_key_pair()
        platform_private, platform_public = _test_key_pair()
        api_v3_key = "0123456789abcdef0123456789abcdef"
        monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "wechat")
        monkeypatch.setattr(settings, "WECHAT_PAY_APP_ID", "wx-app")
        monkeypatch.setattr(settings, "WECHAT_PAY_MCH_ID", "mch-001")
        monkeypatch.setattr(settings, "WECHAT_PAY_SERIAL_NO", "serial-001")
        monkeypatch.setattr(settings, "WECHAT_PAY_PRIVATE_KEY", merchant_private)
        monkeypatch.setattr(settings, "WECHAT_PAY_API_V3_KEY", api_v3_key)
        monkeypatch.setattr(settings, "WECHAT_PAY_PLATFORM_CERT", platform_public)
        monkeypatch.setattr(settings, "WECHAT_PAY_API_BASE_URL", "https://api.mch.weixin.qq.com")
        monkeypatch.setattr(WeChatPaymentProvider, "http_client_factory", _FakeWeChatClient)
        _FakeWeChatClient.calls = []
        headers = _auth_headers(client)

        checkout = client.post(
            "/api/v1/payment/create-checkout-session",
            headers=headers,
            json={
                "provider": "wechat",
                "plan": "monthly",
                "success_url": "http://localhost:5173/payment/success",
                "cancel_url": "http://localhost:5173/payment/cancel",
            },
        )

        assert checkout.status_code == 200
        body = checkout.json()
        assert body["qr_code_url"] == "weixin://wxpay/bizpayurl?pr=test"
        native_call = _FakeWeChatClient.calls[0]
        assert native_call[0].endswith("/v3/pay/transactions/native")
        assert "WECHATPAY2-SHA256-RSA2048" in native_call[1]["headers"]["Authorization"]
        native_body = json.loads(native_call[1]["content"].decode("utf-8"))
        assert native_body["notify_url"] == "http://localhost:8000/api/v1/payment/webhooks/wechat"

        transaction = {
            "transaction_id": "WX_TX_001",
            "out_trade_no": body["merchant_order_id"],
            "trade_state": "SUCCESS",
            "amount": {"total": 990, "payer_total": 990, "currency": "CNY"},
        }
        nonce = "nonce12345678"
        associated_data = "transaction"
        aesgcm = AESGCM(api_v3_key.encode("utf-8"))
        ciphertext = base64.b64encode(
            aesgcm.encrypt(
                nonce.encode("utf-8"),
                json.dumps(transaction, separators=(",", ":")).encode("utf-8"),
                associated_data.encode("utf-8"),
            )
        ).decode("ascii")
        event = {
            "id": "EVT-WX-001",
            "resource": {
                "algorithm": "AEAD_AES_256_GCM",
                "ciphertext": ciphertext,
                "nonce": nonce,
                "associated_data": associated_data,
            },
        }
        body_bytes = json.dumps(event, separators=(",", ":")).encode("utf-8")
        timestamp = "1780000000"
        webhook_nonce = "webhooknonce"
        signature = rsa2_sign(
            platform_private,
            f"{timestamp}\n{webhook_nonce}\n{body_bytes.decode('utf-8')}\n",
        )

        webhook = client.post(
            "/api/v1/payment/webhooks/wechat",
            content=body_bytes,
            headers={
                "wechatpay-timestamp": timestamp,
                "wechatpay-nonce": webhook_nonce,
                "wechatpay-signature": signature,
            },
        )

        assert webhook.status_code == 200
        assert webhook.json()["merchant_order_id"] == body["merchant_order_id"]

    def test_signed_hosted_gateways_cover_epay_and_crypto_providers(self, client, monkeypatch):
        from urllib.parse import parse_qs, urlparse, urlencode

        from app.core.config import settings
        from app.domains.payment.gateways import sign_gateway_params

        gateway_config = {
            "epay": {
                "merchant_id": "epay-pid",
                "secret": "epay-secret",
                "create_url": "https://epay.local/submit.php",
                "notify_url": "http://localhost:8000/api/v1/payment/webhooks/epay",
                "return_url": "http://localhost:5173/payment/success",
                "sign_type": "md5",
            },
            "tokenpay": {
                "merchant_id": "tokenpay-id",
                "secret": "tokenpay-secret",
                "create_url": "https://tokenpay.local/create",
                "sign_type": "hmac-sha256",
                "currency": "USDT",
            },
            "bepusdt": {
                "merchant_id": "bepusdt-id",
                "secret": "bepusdt-secret",
                "create_url": "https://bepusdt.local/create",
            },
            "epusdt": {
                "merchant_id": "epusdt-id",
                "secret": "epusdt-secret",
                "create_url": "https://epusdt.local/create",
            },
            "okpay": {
                "merchant_id": "okpay-id",
                "secret": "okpay-secret",
                "create_url": "https://okpay.local/create",
            },
        }
        monkeypatch.setattr(
            settings,
            "PAYMENT_ENABLED_PROVIDERS_RAW",
            "epay,tokenpay,bepusdt,epusdt,okpay",
        )
        monkeypatch.setattr(settings, "PAYMENT_GATEWAY_CONFIGS_RAW", json.dumps(gateway_config))

        for provider in ["epay", "tokenpay", "bepusdt", "epusdt", "okpay"]:
            headers = _auth_headers(client, email=f"{provider}@example.com")
            checkout = client.post(
                "/api/v1/payment/create-checkout-session",
                headers=headers,
                json={
                    "provider": provider,
                    "plan": "monthly",
                    "success_url": "http://localhost:5173/payment/success",
                    "cancel_url": "http://localhost:5173/payment/cancel",
                },
            )
            assert checkout.status_code == 200
            body = checkout.json()
            parsed = parse_qs(urlparse(body["checkout_url"]).query)
            assert parsed["out_trade_no"] == [body["merchant_order_id"]]
            assert parsed["notify_url"] == [f"http://localhost:8000/api/v1/payment/webhooks/{provider}"]
            assert parsed["return_url"][0].startswith("http://localhost:5173/payment/success")
            assert "sign" in parsed

            notify = {
                "pid": gateway_config[provider]["merchant_id"],
                "out_trade_no": body["merchant_order_id"],
                "trade_no": f"{provider}_trade_001",
                "trade_status": "TRADE_SUCCESS",
                "money": "9.90",
            }
            notify["sign"] = sign_gateway_params(
                notify,
                gateway_config[provider]["secret"],
                gateway_config[provider].get("sign_type", "md5"),
            )
            notify["sign_type"] = gateway_config[provider].get("sign_type", "md5").upper()
            webhook = client.post(
                f"/api/v1/payment/webhooks/{provider}",
                content=urlencode(notify).encode("utf-8"),
                headers={"content-type": "application/x-www-form-urlencoded"},
            )
            assert webhook.status_code == 200
            assert webhook.json()["merchant_order_id"] == body["merchant_order_id"]

    def test_entitlement_changes_only_after_backend_marks_order_paid(self, client, monkeypatch):
        from app.core.config import settings
        from app.core.database import get_db
        from app.domains.payment import PaymentService
        from app.models.user import PaymentOrder, User, UserRole

        monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "epusdt")
        monkeypatch.setattr(
            settings,
            "PAYMENT_GATEWAY_CONFIGS_RAW",
            json.dumps({
                "epusdt": {
                    "merchant_id": "epusdt-id",
                    "secret": "epusdt-secret",
                    "create_url": "https://usdt.local/create",
                }
            }),
        )
        headers = _auth_headers(client)
        checkout = client.post(
            "/api/v1/payment/create-checkout-session",
            headers=headers,
            json={
                "provider": "epusdt",
                "plan": "monthly",
                "success_url": "http://localhost:5173/payment/success",
                "cancel_url": "http://localhost:5173/payment/cancel",
            },
        )
        assert checkout.status_code == 200

        db = next(client.app.dependency_overrides[get_db]())
        try:
            order = db.query(PaymentOrder).filter(
                PaymentOrder.merchant_order_id == checkout.json()["merchant_order_id"]
            ).first()
            user = db.query(User).filter(User.email == "payer@example.com").first()
            assert order.status == "pending"
            assert user.role == UserRole.FREE

            paid_order = PaymentService(db).mark_order_paid(
                merchant_order_id=order.merchant_order_id,
                provider="epusdt",
                provider_order_id="chain_tx_001",
                paid_amount_cents=990,
                currency="USD",
            )
            db.refresh(user)

            assert paid_order.status == "paid"
            assert paid_order.paid_at is not None
            assert user.role == UserRole.PRO
            assert user.subscription_status == "active"
            assert user.subscription_end_date > datetime.utcnow()
        finally:
            db.close()

    def test_duplicate_paid_events_do_not_extend_entitlement_twice(self, client, monkeypatch):
        from app.core.config import settings
        from app.core.database import get_db
        from app.domains.payment.providers import PayPalPaymentProvider
        from app.models.user import PaymentEvent, User

        monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "paypal")
        monkeypatch.setattr(settings, "PAYPAL_CLIENT_ID", "paypal-client")
        monkeypatch.setattr(settings, "PAYPAL_CLIENT_SECRET", "paypal-secret")
        monkeypatch.setattr(settings, "PAYPAL_WEBHOOK_ID", "webhook-id")
        monkeypatch.setattr(PayPalPaymentProvider, "http_client_factory", _FakePayPalClient)
        headers = _auth_headers(client)
        checkout = client.post(
            "/api/v1/payment/create-checkout-session",
            headers=headers,
            json={
                "provider": "paypal",
                "plan": "monthly",
                "success_url": "http://localhost:5173/payment/success",
                "cancel_url": "http://localhost:5173/payment/cancel",
            },
        )
        merchant_order_id = checkout.json()["merchant_order_id"]
        event = {
            "id": "WH-IDEMPOTENT-001",
            "event_type": "PAYMENT.CAPTURE.COMPLETED",
            "resource": {
                "id": "PAYPAL_CAPTURE_IDEMPOTENT",
                "custom_id": merchant_order_id,
                "invoice_id": merchant_order_id,
                "amount": {"currency_code": "USD", "value": "9.90"},
                "supplementary_data": {"related_ids": {"order_id": "PAYPAL_ORDER_001"}},
            },
        }
        webhook_headers = {
            "paypal-auth-algo": "SHA256withRSA",
            "paypal-cert-url": "https://api-m.sandbox.paypal.com/certs/test",
            "paypal-transmission-id": "transmission-idempotent",
            "paypal-transmission-sig": "sig",
            "paypal-transmission-time": "2026-06-12T00:00:00Z",
        }

        first = client.post(
            "/api/v1/payment/webhooks/paypal",
            content=json.dumps(event).encode("utf-8"),
            headers=webhook_headers,
        )
        assert first.status_code == 200

        db = next(client.app.dependency_overrides[get_db]())
        try:
            user = db.query(User).filter(User.email == "payer@example.com").first()
            first_end = user.subscription_end_date
        finally:
            db.close()

        second = client.post(
            "/api/v1/payment/webhooks/paypal",
            content=json.dumps(event).encode("utf-8"),
            headers=webhook_headers,
        )
        assert second.status_code == 200

        db = next(client.app.dependency_overrides[get_db]())
        try:
            user = db.query(User).filter(User.email == "payer@example.com").first()
            assert user.subscription_end_date == first_end
            events = db.query(PaymentEvent).filter(PaymentEvent.provider == "paypal").all()
            assert len([item for item in events if item.provider_event_id == "WH-IDEMPOTENT-001"]) == 1
        finally:
            db.close()

    def test_duplicate_capture_does_not_extend_entitlement_twice(self, client, monkeypatch):
        from app.core.config import settings
        from app.core.database import get_db
        from app.domains.payment.providers import PayPalPaymentProvider
        from app.models.user import PaymentEvent, User

        monkeypatch.setattr(settings, "PAYMENT_ENABLED_PROVIDERS_RAW", "paypal")
        monkeypatch.setattr(settings, "PAYPAL_CLIENT_ID", "paypal-client")
        monkeypatch.setattr(settings, "PAYPAL_CLIENT_SECRET", "paypal-secret")
        monkeypatch.setattr(PayPalPaymentProvider, "http_client_factory", _FakePayPalClient)
        headers = _auth_headers(client)
        checkout = client.post(
            "/api/v1/payment/create-checkout-session",
            headers=headers,
            json={
                "provider": "paypal",
                "plan": "monthly",
                "success_url": "http://localhost:5173/payment/success",
                "cancel_url": "http://localhost:5173/payment/cancel",
            },
        )
        merchant_order_id = checkout.json()["merchant_order_id"]
        _FakePayPalClient.current_merchant_order_id = merchant_order_id

        first = client.post(
            f"/api/v1/payment/orders/{merchant_order_id}/capture",
            headers=headers,
        )
        assert first.status_code == 200

        db = next(client.app.dependency_overrides[get_db]())
        try:
            user = db.query(User).filter(User.email == "payer@example.com").first()
            first_end = user.subscription_end_date
        finally:
            db.close()

        second = client.post(
            f"/api/v1/payment/orders/{merchant_order_id}/capture",
            headers=headers,
        )
        assert second.status_code == 200

        db = next(client.app.dependency_overrides[get_db]())
        try:
            user = db.query(User).filter(User.email == "payer@example.com").first()
            assert user.subscription_end_date == first_end
            assert db.query(PaymentEvent).filter(
                PaymentEvent.provider == "paypal",
                PaymentEvent.provider_event_id == "PAYPAL_CAPTURE_001",
            ).count() == 1
        finally:
            db.close()
