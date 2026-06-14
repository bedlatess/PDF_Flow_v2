"""Payment provider adapters.

The endpoint layer should not know how PayPal, Alipay, WeChat Pay, EPay,
TokenPay, BEPUSDT, EPUSDT, or OKPay shape their requests. Each provider adapter
normalizes those differences into the same order and webhook contracts.
"""

from __future__ import annotations

import json
import time
import hashlib
from datetime import datetime
from dataclasses import dataclass
from typing import Mapping, Protocol
from uuid import uuid4

import httpx
import stripe

from app.core.config import settings
from app.domains.payment.crypto import (
    aesgcm_decrypt_base64,
    canonical_query,
    form_urlencode,
    rsa2_sign,
    rsa2_verify,
    wechat_pay_sign,
    wechat_pay_verify,
)
from app.domains.payment.gateways import (
    build_gateway_url,
    parse_gateway_config,
    sign_gateway_params,
)


SUPPORTED_PAYMENT_PROVIDERS = (
    "stripe",
    "paypal",
    "epay",
    "alipay",
    "wechat",
    "tokenpay",
    "bepusdt",
    "epusdt",
    "okpay",
    "gmpay",
)

REDIRECT_PROVIDERS = {"stripe", "paypal", "epay", "alipay"}
QR_PROVIDERS = {"wechat", "tokenpay", "bepusdt", "epusdt", "okpay", "gmpay"}


@dataclass(frozen=True)
class PaymentProviderConfig:
    key: str
    enabled: bool
    display_name: str
    settlement: str
    supports_subscription: bool = False
    supports_one_time: bool = True


@dataclass(frozen=True)
class PaymentCreateResult:
    provider_order_id: str
    checkout_url: str | None = None
    qr_code_url: str | None = None
    raw_payload: dict | None = None


@dataclass(frozen=True)
class NormalizedPaymentEvent:
    provider: str
    provider_event_id: str
    merchant_order_id: str
    provider_order_id: str | None
    status: str
    paid_amount_cents: int | None = None
    currency: str | None = None
    raw_payload: dict | None = None


class PaymentProvider(Protocol):
    key: str

    def create_order(
        self,
        *,
        merchant_order_id: str,
        plan: str,
        amount_cents: int,
        currency: str,
        user_email: str,
        success_url: str,
        cancel_url: str,
        notification_url: str,
    ) -> PaymentCreateResult:
        ...

    def verify_webhook(
        self,
        *,
        headers: Mapping[str, str],
        body: bytes,
        query: Mapping[str, str],
    ) -> NormalizedPaymentEvent:
        ...

    def capture_order(self, *, provider_order_id: str) -> NormalizedPaymentEvent:
        ...


class ConfigurableHostedPaymentProvider:
    """Provider stub for gateways that return a hosted checkout or QR URL.

    Production adapters will replace this class with exact HTTP signing and
    verification logic for each gateway. Until credentials are configured, this
    gives tests and frontend flows a stable contract without pretending money
    has been collected.
    """

    def __init__(self, key: str, base_checkout_url: str | None = None):
        self.key = key
        self.base_checkout_url = base_checkout_url

    def create_order(
        self,
        *,
        merchant_order_id: str,
        plan: str,
        amount_cents: int,
        currency: str,
        user_email: str,
        success_url: str,
        cancel_url: str,
        notification_url: str,
    ) -> PaymentCreateResult:
        provider_order_id = f"{self.key}_{uuid4().hex[:18]}"
        checkout_url = (
            f"{self.base_checkout_url.rstrip('/')}/checkout/{provider_order_id}"
            if self.base_checkout_url
            else None
        )
        qr_code_url = None
        if self.key in QR_PROVIDERS and checkout_url:
            qr_code_url = checkout_url

        return PaymentCreateResult(
            provider_order_id=provider_order_id,
            checkout_url=checkout_url,
            qr_code_url=qr_code_url,
            raw_payload={
                "provider": self.key,
                "merchant_order_id": merchant_order_id,
                "plan": plan,
                "amount_cents": amount_cents,
                "currency": currency,
                "user_email": user_email,
                "success_url": success_url,
                "cancel_url": cancel_url,
                "notification_url": notification_url,
                "mode": "hosted_stub",
            },
        )

    def verify_webhook(
        self,
        *,
        headers: Mapping[str, str],
        body: bytes,
        query: Mapping[str, str],
    ) -> NormalizedPaymentEvent:
        raise NotImplementedError(f"{self.key} webhook verification is not configured")

    def capture_order(self, *, provider_order_id: str) -> NormalizedPaymentEvent:
        raise NotImplementedError(f"{self.key} capture is not configured")


def build_gmpay_signature(params: Mapping[str, object], secret_key: str) -> str:
    canonical = "&".join(
        f"{field}={params[field]}"
        for field in sorted(params)
        if field != "signature" and params.get(field) not in (None, "")
    )
    return hashlib.md5(f"{canonical}{secret_key}".encode("utf-8")).hexdigest().lower()


class GMPayPaymentProvider:
    """GM Pay hosted checkout adapter.

    Phase 1 intentionally does not apply webhook-paid events until a real GM Pay
    callback sample is available and strict verification is implemented.
    """

    key = "gmpay"
    http_client_factory = httpx.Client

    def __init__(self, *, public_config: dict, secrets: dict):
        self.public_config = dict(public_config)
        self.secrets = dict(secrets)

    def create_order(
        self,
        *,
        merchant_order_id: str,
        plan: str,
        amount_cents: int,
        currency: str,
        user_email: str,
        success_url: str,
        cancel_url: str,
        notification_url: str,
    ) -> PaymentCreateResult:
        api_base_url = str(self.public_config.get("api_base_url") or "").rstrip("/")
        pid = str(self.public_config.get("pid") or "").strip()
        secret_key = str(self.secrets.get("secret_key") or "").strip()
        if not api_base_url or not pid or not secret_key:
            raise RuntimeError("GM Pay gateway is not configured")

        name = f"PDF-Flow Pro {plan}"
        amount = self._money_value(amount_cents)
        payload = {
            "pid": pid,
            "order_id": merchant_order_id,
            "currency": str(currency or self.public_config.get("currency") or "cny").lower(),
            "token": str(self.public_config.get("token") or "usdt").lower(),
            "network": str(self.public_config.get("network") or "tron").lower(),
            "amount": amount,
            "notify_url": notification_url,
            "name": name,
        }
        payload["signature"] = build_gmpay_signature(payload, secret_key)

        with self.http_client_factory(timeout=15.0) as client:
            response = client.post(
                f"{api_base_url}/payments/gmpay/v1/order/create-transaction",
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()

        transaction = data.get("data") if isinstance(data.get("data"), dict) else data
        payment_url = (
            transaction.get("payment_url")
            or transaction.get("checkout_url")
            or transaction.get("pay_url")
        )
        provider_order_id = (
            transaction.get("trade_id")
            or transaction.get("transaction_id")
            or transaction.get("id")
            or merchant_order_id
        )
        if not payment_url:
            raise RuntimeError("GM Pay did not return payment_url")

        return PaymentCreateResult(
            provider_order_id=str(provider_order_id),
            checkout_url=str(payment_url),
            qr_code_url=str(payment_url),
            raw_payload={"provider": "gmpay", "mode": "hosted_checkout"},
        )

    def verify_webhook(
        self,
        *,
        headers: Mapping[str, str],
        body: bytes,
        query: Mapping[str, str],
    ) -> NormalizedPaymentEvent:
        payload = self._parse_payload(body, query)
        merchant_order_id = str(payload.get("order_id") or payload.get("merchant_order_id") or "")
        provider_order_id = str(payload.get("trade_id") or payload.get("transaction_id") or "")
        event_id = provider_order_id or merchant_order_id or f"gmpay_unverified_{uuid4().hex[:16]}"
        return NormalizedPaymentEvent(
            provider="gmpay",
            provider_event_id=event_id,
            merchant_order_id=merchant_order_id,
            provider_order_id=provider_order_id or None,
            status="accepted",
            paid_amount_cents=None,
            currency=str(payload.get("currency") or self.public_config.get("currency") or "").upper() or None,
            raw_payload={"status": "webhook_skeleton_no_entitlement"},
        )

    def capture_order(self, *, provider_order_id: str) -> NormalizedPaymentEvent:
        raise NotImplementedError("GM Pay orders are completed by webhook after strict verification")

    @staticmethod
    def _money_value(amount_cents: int) -> str:
        return f"{amount_cents / 100:.2f}"

    @staticmethod
    def _parse_payload(body: bytes, query: Mapping[str, str]) -> dict:
        from urllib.parse import parse_qsl

        if body:
            text = body.decode("utf-8")
            if text.strip().startswith("{"):
                return json.loads(text)
            return dict(parse_qsl(text, keep_blank_values=True))
        return dict(query)


class SignedHostedGatewayProvider:
    """MD5/HMAC signed hosted gateway for EPay and USDT-style providers."""

    def __init__(self, key: str, config: dict | None = None):
        self.key = key
        self.config = parse_gateway_config(key, config)

    def create_order(
        self,
        *,
        merchant_order_id: str,
        plan: str,
        amount_cents: int,
        currency: str,
        user_email: str,
        success_url: str,
        cancel_url: str,
        notification_url: str,
    ) -> PaymentCreateResult:
        if not self.config.merchant_id or not self.config.secret or not self.config.create_url:
            raise RuntimeError(f"{self.key} gateway is not configured")

        params = {
            "pid": self.config.merchant_id,
            "out_trade_no": merchant_order_id,
            "type": self.config.extra.get("type", "usdt" if self.key != "epay" else "alipay"),
            "name": f"PDF-Flow Pro {plan}",
            "money": self._money_value(amount_cents),
            "notify_url": self.config.notify_url or notification_url,
            "return_url": self.config.return_url or success_url,
            "clientip": self.config.extra.get("clientip"),
            "currency": self.config.currency if self.key != "epay" else None,
        }
        params.update(self.config.extra)
        params = {key: value for key, value in params.items() if value is not None}
        params["sign"] = sign_gateway_params(params, self.config.secret, self.config.sign_type)
        params["sign_type"] = self.config.sign_type.upper()
        checkout_url = build_gateway_url(self.config.create_url, params)

        return PaymentCreateResult(
            provider_order_id=f"{self.key}_{merchant_order_id}",
            checkout_url=checkout_url,
            qr_code_url=checkout_url if self.key in QR_PROVIDERS else None,
            raw_payload={"provider": self.key, "sign_type": self.config.sign_type},
        )

    def verify_webhook(
        self,
        *,
        headers: Mapping[str, str],
        body: bytes,
        query: Mapping[str, str],
    ) -> NormalizedPaymentEvent:
        params = dict(query)
        if body:
            params.update(self._parse_body(body))
        expected = sign_gateway_params(params, self.config.secret, self.config.sign_type)
        if (params.get("sign") or "").lower() != expected.lower():
            raise RuntimeError(f"{self.key} signature verification failed")

        status_value = str(params.get("trade_status") or params.get("status") or "").upper()
        paid = status_value in {"TRADE_SUCCESS", "TRADE_FINISHED", "SUCCESS", "PAID", "COMPLETED", "1"}
        amount_value = params.get("money") or params.get("amount") or params.get("actual_amount")
        return NormalizedPaymentEvent(
            provider=self.key,
            provider_event_id=str(params.get("trade_no") or params.get("transaction_id") or ""),
            merchant_order_id=str(params.get("out_trade_no") or params.get("order_id") or ""),
            provider_order_id=str(params.get("trade_no") or params.get("transaction_id") or ""),
            status="paid" if paid else "accepted",
            paid_amount_cents=self._cents(amount_value),
            currency=str(params.get("currency") or self.config.currency),
            raw_payload={"status": status_value},
        )

    def capture_order(self, *, provider_order_id: str) -> NormalizedPaymentEvent:
        raise NotImplementedError(f"{self.key} gateway is completed by webhook")

    @staticmethod
    def _money_value(amount_cents: int) -> str:
        return f"{amount_cents / 100:.2f}"

    @staticmethod
    def _cents(value: str | None) -> int | None:
        if value is None:
            return None
        return int(round(float(value) * 100))

    @staticmethod
    def _parse_body(body: bytes) -> dict:
        from urllib.parse import parse_qsl

        content = body.decode("utf-8")
        if not content:
            return {}
        if content.strip().startswith("{"):
            return json.loads(content)
        return dict(parse_qsl(content, keep_blank_values=True))


class StripePaymentProvider:
    key = "stripe"

    def create_order(
        self,
        *,
        merchant_order_id: str,
        plan: str,
        amount_cents: int,
        currency: str,
        user_email: str,
        success_url: str,
        cancel_url: str,
        notification_url: str,
    ) -> PaymentCreateResult:
        if not settings.STRIPE_SECRET_KEY:
            raise RuntimeError("Stripe secret key is not configured")

        price_id = {
            "monthly": settings.STRIPE_PRICE_ID_MONTHLY,
            "yearly": settings.STRIPE_PRICE_ID_YEARLY,
        }.get(plan)
        if not price_id:
            raise RuntimeError(f"Stripe price ID for {plan} is not configured")

        stripe.api_key = settings.STRIPE_SECRET_KEY
        checkout_session = stripe.checkout.Session.create(
            customer_email=user_email,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=self._append_query(success_url, f"session_id={{CHECKOUT_SESSION_ID}}"),
            cancel_url=cancel_url,
            metadata={
                "merchant_order_id": merchant_order_id,
                "plan": plan,
                "amount_cents": str(amount_cents),
                "currency": currency,
            },
        )
        return PaymentCreateResult(
            provider_order_id=checkout_session.id,
            checkout_url=checkout_session.url,
            raw_payload={"stripe_session_id": checkout_session.id},
        )

    def verify_webhook(
        self,
        *,
        headers: Mapping[str, str],
        body: bytes,
        query: Mapping[str, str],
    ) -> NormalizedPaymentEvent:
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise RuntimeError("Stripe webhook secret is not configured")

        stripe.api_key = settings.STRIPE_SECRET_KEY
        event = stripe.Webhook.construct_event(
            body,
            headers.get("stripe-signature"),
            settings.STRIPE_WEBHOOK_SECRET,
        )
        event_type = event["type"]
        data = event["data"]["object"]
        metadata = data.get("metadata") or {}

        return NormalizedPaymentEvent(
            provider="stripe",
            provider_event_id=event.get("id", ""),
            merchant_order_id=metadata.get("merchant_order_id", ""),
            provider_order_id=data.get("id"),
            status="paid" if event_type == "checkout.session.completed" else "accepted",
            paid_amount_cents=data.get("amount_total"),
            currency=(data.get("currency") or "").upper() or None,
            raw_payload={"type": event_type},
        )

    def capture_order(self, *, provider_order_id: str) -> NormalizedPaymentEvent:
        raise NotImplementedError("Stripe checkout is completed by webhook, not capture")

    @staticmethod
    def _append_query(url: str, query: str) -> str:
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}{query}"


class PayPalPaymentProvider:
    key = "paypal"
    http_client_factory = httpx.Client

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or settings.PAYPAL_API_BASE_URL).rstrip("/")

    def create_order(
        self,
        *,
        merchant_order_id: str,
        plan: str,
        amount_cents: int,
        currency: str,
        user_email: str,
        success_url: str,
        cancel_url: str,
        notification_url: str,
    ) -> PaymentCreateResult:
        token = self._access_token()
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": merchant_order_id,
                    "custom_id": merchant_order_id,
                    "invoice_id": merchant_order_id,
                    "description": f"PDF-Flow Pro {plan}",
                    "amount": {
                        "currency_code": currency,
                        "value": self._money_value(amount_cents),
                    },
                }
            ],
            "application_context": {
                "brand_name": "PDF-Flow",
                "landing_page": "LOGIN",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "PAY_NOW",
                "return_url": success_url,
                "cancel_url": cancel_url,
            },
        }

        with self.http_client_factory(timeout=15.0) as client:
            response = client.post(
                f"{self.base_url}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "PayPal-Request-Id": merchant_order_id,
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        approval_url = self._approval_url(data)
        if not approval_url:
            raise RuntimeError("PayPal order did not include an approval URL")

        return PaymentCreateResult(
            provider_order_id=data["id"],
            checkout_url=approval_url,
            raw_payload={
                "paypal_order_id": data["id"],
                "status": data.get("status"),
            },
        )

    def capture_order(self, *, provider_order_id: str) -> NormalizedPaymentEvent:
        token = self._access_token()
        with self.http_client_factory(timeout=15.0) as client:
            response = client.post(
                f"{self.base_url}/v2/checkout/orders/{provider_order_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        capture = self._first_capture(data)
        if not capture:
            raise RuntimeError("PayPal capture response did not include a capture")

        amount = capture.get("amount") or {}
        return NormalizedPaymentEvent(
            provider="paypal",
            provider_event_id=capture.get("id") or data.get("id") or "",
            merchant_order_id=self._merchant_order_id(data),
            provider_order_id=data.get("id"),
            status="paid" if capture.get("status") == "COMPLETED" else "accepted",
            paid_amount_cents=self._cents(amount.get("value")),
            currency=amount.get("currency_code"),
            raw_payload={"status": data.get("status"), "capture_status": capture.get("status")},
        )

    def verify_webhook(
        self,
        *,
        headers: Mapping[str, str],
        body: bytes,
        query: Mapping[str, str],
    ) -> NormalizedPaymentEvent:
        if not settings.PAYPAL_WEBHOOK_ID:
            raise RuntimeError("PayPal webhook id is not configured")

        event = self._parse_json(body)
        token = self._access_token()
        verify_payload = {
            "auth_algo": headers.get("paypal-auth-algo"),
            "cert_url": headers.get("paypal-cert-url"),
            "transmission_id": headers.get("paypal-transmission-id"),
            "transmission_sig": headers.get("paypal-transmission-sig"),
            "transmission_time": headers.get("paypal-transmission-time"),
            "webhook_id": settings.PAYPAL_WEBHOOK_ID,
            "webhook_event": event,
        }

        with self.http_client_factory(timeout=15.0) as client:
            response = client.post(
                f"{self.base_url}/v1/notifications/verify-webhook-signature",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=verify_payload,
            )
            response.raise_for_status()
            verification = response.json()

        if verification.get("verification_status") != "SUCCESS":
            raise RuntimeError("PayPal webhook signature verification failed")

        resource = event.get("resource") or {}
        amount = resource.get("amount") or resource.get("seller_receivable_breakdown", {}).get("gross_amount") or {}
        return NormalizedPaymentEvent(
            provider="paypal",
            provider_event_id=event.get("id", ""),
            merchant_order_id=resource.get("custom_id") or resource.get("invoice_id") or "",
            provider_order_id=resource.get("supplementary_data", {})
            .get("related_ids", {})
            .get("order_id"),
            status="paid" if event.get("event_type") == "PAYMENT.CAPTURE.COMPLETED" else "accepted",
            paid_amount_cents=self._cents(amount.get("value")),
            currency=amount.get("currency_code"),
            raw_payload={"type": event.get("event_type")},
        )

    def _access_token(self) -> str:
        if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
            raise RuntimeError("PayPal credentials are not configured")

        with self.http_client_factory(timeout=15.0) as client:
            response = client.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json", "Accept-Language": "en_US"},
            )
            response.raise_for_status()
            data = response.json()

        token = data.get("access_token")
        if not token:
            raise RuntimeError("PayPal token response did not include an access token")
        return token

    @staticmethod
    def _money_value(amount_cents: int) -> str:
        return f"{amount_cents / 100:.2f}"

    @staticmethod
    def _cents(value: str | None) -> int | None:
        if value is None:
            return None
        return int(round(float(value) * 100))

    @staticmethod
    def _approval_url(data: dict) -> str | None:
        for link in data.get("links") or []:
            if link.get("rel") == "approve":
                return link.get("href")
        return None

    @staticmethod
    def _first_capture(data: dict) -> dict | None:
        for purchase_unit in data.get("purchase_units") or []:
            payments = purchase_unit.get("payments") or {}
            captures = payments.get("captures") or []
            if captures:
                return captures[0]
        return None

    @staticmethod
    def _merchant_order_id(data: dict) -> str:
        purchase_units = data.get("purchase_units") or []
        if not purchase_units:
            return ""
        unit = purchase_units[0]
        return unit.get("custom_id") or unit.get("invoice_id") or unit.get("reference_id") or ""

    @staticmethod
    def _parse_json(body: bytes) -> dict:
        import json

        return json.loads(body.decode("utf-8"))


class AlipayPaymentProvider:
    key = "alipay"

    def create_order(
        self,
        *,
        merchant_order_id: str,
        plan: str,
        amount_cents: int,
        currency: str,
        user_email: str,
        success_url: str,
        cancel_url: str,
        notification_url: str,
    ) -> PaymentCreateResult:
        if not settings.ALIPAY_APP_ID or not settings.ALIPAY_PRIVATE_KEY:
            raise RuntimeError("Alipay credentials are not configured")

        biz_content = {
            "out_trade_no": merchant_order_id,
            "product_code": "FAST_INSTANT_TRADE_PAY",
            "total_amount": self._money_value(amount_cents),
            "subject": f"PDF-Flow Pro {plan}",
        }
        params = {
            "app_id": settings.ALIPAY_APP_ID,
            "method": "alipay.trade.page.pay",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "return_url": success_url,
            "notify_url": notification_url,
            "biz_content": json.dumps(biz_content, ensure_ascii=False, separators=(",", ":")),
        }
        sign_content = canonical_query(params, exclude={"sign"})
        params["sign"] = rsa2_sign(settings.ALIPAY_PRIVATE_KEY, sign_content)
        checkout_url = f"{settings.ALIPAY_GATEWAY_URL}?{form_urlencode(params)}"

        return PaymentCreateResult(
            provider_order_id=merchant_order_id,
            checkout_url=checkout_url,
            raw_payload={"method": "alipay.trade.page.pay"},
        )

    def verify_webhook(
        self,
        *,
        headers: Mapping[str, str],
        body: bytes,
        query: Mapping[str, str],
    ) -> NormalizedPaymentEvent:
        if not settings.ALIPAY_PUBLIC_KEY:
            raise RuntimeError("Alipay public key is not configured")
        params = self._parse_body(body) if body else dict(query)
        sign = params.get("sign")
        if not sign:
            raise RuntimeError("Alipay notification did not include a signature")
        sign_content = canonical_query(params, exclude={"sign", "sign_type"})
        if not rsa2_verify(settings.ALIPAY_PUBLIC_KEY, sign_content, sign):
            raise RuntimeError("Alipay signature verification failed")

        trade_status = str(params.get("trade_status") or "")
        return NormalizedPaymentEvent(
            provider="alipay",
            provider_event_id=str(params.get("trade_no") or ""),
            merchant_order_id=str(params.get("out_trade_no") or ""),
            provider_order_id=str(params.get("trade_no") or ""),
            status="paid" if trade_status in {"TRADE_SUCCESS", "TRADE_FINISHED"} else "accepted",
            paid_amount_cents=self._cents(params.get("total_amount") or params.get("receipt_amount")),
            currency="CNY",
            raw_payload={"trade_status": trade_status},
        )

    def capture_order(self, *, provider_order_id: str) -> NormalizedPaymentEvent:
        raise NotImplementedError("Alipay page pay is completed by notification")

    @staticmethod
    def _money_value(amount_cents: int) -> str:
        return f"{amount_cents / 100:.2f}"

    @staticmethod
    def _cents(value: str | None) -> int | None:
        if value is None:
            return None
        return int(round(float(value) * 100))

    @staticmethod
    def _parse_body(body: bytes) -> dict:
        from urllib.parse import parse_qsl

        return dict(parse_qsl(body.decode("utf-8"), keep_blank_values=True))


class WeChatPaymentProvider:
    key = "wechat"
    http_client_factory = httpx.Client

    def create_order(
        self,
        *,
        merchant_order_id: str,
        plan: str,
        amount_cents: int,
        currency: str,
        user_email: str,
        success_url: str,
        cancel_url: str,
        notification_url: str,
    ) -> PaymentCreateResult:
        self._require_create_config()
        path = "/v3/pay/transactions/native"
        body = {
            "appid": settings.WECHAT_PAY_APP_ID,
            "mchid": settings.WECHAT_PAY_MCH_ID,
            "description": f"PDF-Flow Pro {plan}",
            "out_trade_no": merchant_order_id,
            "notify_url": notification_url,
            "amount": {"total": amount_cents, "currency": "CNY"},
        }
        body_json = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
        authorization = self._authorization("POST", path, body_json)

        with self.http_client_factory(timeout=15.0) as client:
            response = client.post(
                f"{settings.WECHAT_PAY_API_BASE_URL.rstrip('/')}{path}",
                headers={
                    "Authorization": authorization,
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                content=body_json.encode("utf-8"),
            )
            response.raise_for_status()
            data = response.json()

        code_url = data.get("code_url")
        if not code_url:
            raise RuntimeError("WeChat Pay did not return code_url")
        return PaymentCreateResult(
            provider_order_id=merchant_order_id,
            checkout_url=code_url,
            qr_code_url=code_url,
            raw_payload={"mode": "native"},
        )

    def verify_webhook(
        self,
        *,
        headers: Mapping[str, str],
        body: bytes,
        query: Mapping[str, str],
    ) -> NormalizedPaymentEvent:
        self._require_webhook_config()
        if not wechat_pay_verify(
            settings.WECHAT_PAY_PLATFORM_CERT,
            headers.get("wechatpay-timestamp", ""),
            headers.get("wechatpay-nonce", ""),
            body,
            headers.get("wechatpay-signature", ""),
        ):
            raise RuntimeError("WeChat Pay signature verification failed")

        event = json.loads(body.decode("utf-8"))
        resource = event.get("resource") or {}
        plaintext = aesgcm_decrypt_base64(
            settings.WECHAT_PAY_API_V3_KEY,
            resource.get("nonce", ""),
            resource.get("ciphertext", ""),
            resource.get("associated_data", ""),
        )
        transaction = json.loads(plaintext.decode("utf-8"))
        amount = transaction.get("amount") or {}
        trade_state = transaction.get("trade_state")
        return NormalizedPaymentEvent(
            provider="wechat",
            provider_event_id=str(transaction.get("transaction_id") or event.get("id") or ""),
            merchant_order_id=str(transaction.get("out_trade_no") or ""),
            provider_order_id=str(transaction.get("transaction_id") or ""),
            status="paid" if trade_state == "SUCCESS" else "accepted",
            paid_amount_cents=amount.get("payer_total") or amount.get("total"),
            currency=amount.get("currency") or "CNY",
            raw_payload={"trade_state": trade_state},
        )

    def capture_order(self, *, provider_order_id: str) -> NormalizedPaymentEvent:
        raise NotImplementedError("WeChat Pay native orders are completed by notification")

    def _authorization(self, method: str, path: str, body: str) -> str:
        timestamp = str(int(time.time()))
        nonce = uuid4().hex
        signature = wechat_pay_sign(settings.WECHAT_PAY_PRIVATE_KEY, method, path, timestamp, nonce, body)
        return (
            'WECHATPAY2-SHA256-RSA2048 '
            f'mchid="{settings.WECHAT_PAY_MCH_ID}",'
            f'nonce_str="{nonce}",'
            f'timestamp="{timestamp}",'
            f'serial_no="{settings.WECHAT_PAY_SERIAL_NO}",'
            f'signature="{signature}"'
        )

    @staticmethod
    def _require_create_config() -> None:
        required = [
            settings.WECHAT_PAY_APP_ID,
            settings.WECHAT_PAY_MCH_ID,
            settings.WECHAT_PAY_SERIAL_NO,
            settings.WECHAT_PAY_PRIVATE_KEY,
        ]
        if not all(required):
            raise RuntimeError("WeChat Pay create-order credentials are not configured")

    @staticmethod
    def _require_webhook_config() -> None:
        required = [
            settings.WECHAT_PAY_PLATFORM_CERT,
            settings.WECHAT_PAY_API_V3_KEY,
        ]
        if not all(required):
            raise RuntimeError("WeChat Pay webhook credentials are not configured")


class PaymentProviderRegistry:
    def __init__(self, providers: Mapping[str, PaymentProvider]):
        self._providers = dict(providers)

    def get(self, provider: str) -> PaymentProvider:
        try:
            return self._providers[provider]
        except KeyError as exc:
            raise ValueError(f"Unsupported payment provider: {provider}") from exc

    def available(self) -> list[str]:
        return sorted(self._providers)


def provider_display_name(provider: str) -> str:
    return {
        "stripe": "Stripe",
        "paypal": "PayPal",
        "epay": "易支付",
        "alipay": "支付宝",
        "wechat": "微信支付",
        "tokenpay": "TokenPay",
        "bepusdt": "BEPUSDT",
        "epusdt": "EPUSDT",
        "okpay": "OKPay",
        "gmpay": "GM Pay",
    }.get(provider, provider)
