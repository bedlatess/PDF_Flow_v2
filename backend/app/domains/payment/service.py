"""Payment application service.

This service owns the trustworthy payment state machine. Frontend routes can
start a checkout and render status, but plan activation must flow through order
state and verified provider notifications here.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Mapping
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.payment.config_store import (
    get_provider_runtime_config,
    list_managed_payment_provider_keys,
)
from app.domains.payment.providers import (
    AlipayPaymentProvider,
    ConfigurableHostedPaymentProvider,
    GMPayPaymentProvider,
    PayPalPaymentProvider,
    PaymentProviderConfig,
    PaymentProviderRegistry,
    SignedHostedGatewayProvider,
    StripePaymentProvider,
    WeChatPaymentProvider,
    provider_display_name,
)
from app.models.user import PaymentEvent, PaymentOrder, PaymentProviderAccount, User, UserRole


PLAN_CATALOG = {
    "monthly": {"amount_cents": 990, "currency": "USD", "period_days": 30},
    "yearly": {"amount_cents": 7900, "currency": "USD", "period_days": 365},
}

PROVIDER_CURRENCY = {
    "alipay": "CNY",
    "wechat": "CNY",
}

PUBLIC_CHECKOUT_PROVIDER_KEYS = ("stripe", "paypal", "gmpay")


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self._runtime_configs = self._load_runtime_configs()
        self.registry = PaymentProviderRegistry(self._build_providers())

    def _load_runtime_configs(self) -> dict:
        configs = {}
        for key in list_managed_payment_provider_keys():
            try:
                runtime_config = get_provider_runtime_config(self.db, key)
            except HTTPException:
                runtime_config = None
            if runtime_config:
                configs[key] = runtime_config
        return configs

    def _build_providers(self) -> dict:
        gateway_urls = settings.PAYMENT_PROVIDER_CHECKOUT_URLS
        providers = {}
        gmpay_config = self._runtime_configs.get("gmpay")
        if gmpay_config:
            providers["gmpay"] = GMPayPaymentProvider(
                public_config=gmpay_config["public_config"],
                secrets=gmpay_config["secrets"],
            )
        stripe_config = self._runtime_configs.get("stripe")
        if stripe_config:
            providers["stripe"] = StripePaymentProvider(
                public_config=stripe_config["public_config"],
                secrets=stripe_config["secrets"],
            )
        paypal_config = self._runtime_configs.get("paypal")
        if paypal_config:
            providers["paypal"] = PayPalPaymentProvider(
                public_config=paypal_config["public_config"],
                secrets=paypal_config["secrets"],
            )
        for key in settings.PAYMENT_ENABLED_PROVIDERS:
            if key in providers:
                continue
            if key == "stripe":
                providers[key] = StripePaymentProvider()
            elif key == "paypal":
                providers[key] = PayPalPaymentProvider()
            elif key == "alipay":
                providers[key] = AlipayPaymentProvider()
            elif key == "wechat":
                providers[key] = WeChatPaymentProvider()
            elif key in {"epay", "tokenpay", "bepusdt", "epusdt", "okpay"}:
                providers[key] = SignedHostedGatewayProvider(
                    key,
                    settings.PAYMENT_GATEWAY_CONFIGS.get(key),
                )
            else:
                providers[key] = ConfigurableHostedPaymentProvider(key, gateway_urls.get(key))
        return providers

    def list_providers(self) -> list[PaymentProviderConfig]:
        enabled = set(settings.PAYMENT_ENABLED_PROVIDERS)
        provider_order = [
            key for key in settings.PAYMENT_PROVIDER_ORDER
            if key in PUBLIC_CHECKOUT_PROVIDER_KEYS
        ]
        for key in self._runtime_configs:
            if key in PUBLIC_CHECKOUT_PROVIDER_KEYS and key not in provider_order:
                provider_order.append(key)
        if not provider_order:
            provider_order = list(PUBLIC_CHECKOUT_PROVIDER_KEYS)
        providers = [
            PaymentProviderConfig(
                key=key,
                enabled=key in enabled or key in self._runtime_configs,
                display_name=provider_display_name(key),
                settlement="subscription" if key == "stripe" else "one_time_entitlement",
                supports_subscription=key == "stripe",
                supports_one_time=True,
            )
            for key in provider_order
        ]
        return providers

    def create_checkout_order(
        self,
        *,
        user: User,
        provider: str,
        plan: str,
        success_url: str,
        cancel_url: str,
    ) -> PaymentOrder:
        if provider not in self.registry.available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{provider_display_name(provider)} payment is not enabled",
            )

        if plan not in PLAN_CATALOG:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan. Must be 'monthly' or 'yearly'",
            )

        catalog_item = PLAN_CATALOG[plan]
        order_ttl_minutes = settings.PAYMENT_ORDER_TTL_MINUTES
        if provider == "gmpay":
            runtime_config = self._runtime_configs.get("gmpay")
            public_config = runtime_config["public_config"] if runtime_config else {}
            amount_key = "monthly_amount_cents" if plan == "monthly" else "yearly_amount_cents"
            catalog_item = {
                "amount_cents": int(public_config.get(amount_key) or catalog_item["amount_cents"]),
                "currency": str(public_config.get("currency") or catalog_item["currency"]).upper(),
                "period_days": PLAN_CATALOG[plan]["period_days"],
            }
            order_ttl_minutes = int(public_config.get("order_ttl_minutes") or order_ttl_minutes)
        gateway_config = settings.PAYMENT_GATEWAY_CONFIGS.get(provider, {})
        currency = PROVIDER_CURRENCY.get(provider, gateway_config.get("currency", catalog_item["currency"]))
        merchant_order_id = f"pf_{datetime.utcnow():%Y%m%d}_{uuid4().hex[:18]}"
        provider_adapter = self.registry.get(provider)
        notification_url = self._provider_webhook_url(provider)
        try:
            provider_result = provider_adapter.create_order(
                merchant_order_id=merchant_order_id,
                plan=plan,
                amount_cents=catalog_item["amount_cents"],
                currency=currency,
                user_email=user.email,
                success_url=self._success_return_url(success_url, provider, merchant_order_id),
                cancel_url=cancel_url,
                notification_url=notification_url,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{provider_display_name(provider)} payment is not configured",
            ) from exc

        order = PaymentOrder(
            user_id=user.id,
            provider=provider,
            merchant_order_id=merchant_order_id,
            provider_order_id=provider_result.provider_order_id,
            plan=plan,
            amount_cents=catalog_item["amount_cents"],
            currency=currency,
            status="pending",
            checkout_url=provider_result.checkout_url,
            qr_code_url=provider_result.qr_code_url,
            expires_at=datetime.utcnow() + timedelta(minutes=order_ttl_minutes),
        )
        self.db.add(order)
        self._ensure_provider_account(user, provider)
        self.db.commit()
        self.db.refresh(order)
        return order

    def capture_checkout_order(self, *, user: User, merchant_order_id: str) -> PaymentOrder:
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.merchant_order_id == merchant_order_id,
            PaymentOrder.user_id == user.id,
        ).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment order not found")
        if order.status == "paid":
            return order

        provider_adapter = self.registry.get(order.provider)
        try:
            event = provider_adapter.capture_order(provider_order_id=order.provider_order_id)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{provider_display_name(order.provider)} capture failed",
            ) from exc

        if event.status != "paid":
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Payment capture accepted but not completed",
            )

        return self._apply_paid_event(event)

    def mark_order_paid(
        self,
        *,
        merchant_order_id: str,
        provider: str,
        provider_order_id: str | None = None,
        paid_amount_cents: int | None = None,
        currency: str | None = None,
    ) -> PaymentOrder:
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.merchant_order_id == merchant_order_id,
            PaymentOrder.provider == provider,
        ).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment order not found")

        if order.status == "paid":
            return order

        if paid_amount_cents is not None and paid_amount_cents != order.amount_cents:
            order.status = "amount_mismatch"
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment amount mismatch")

        if currency is not None and currency.upper() != order.currency.upper():
            order.status = "currency_mismatch"
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment currency mismatch")

        order.status = "paid"
        order.provider_order_id = provider_order_id or order.provider_order_id
        order.paid_at = datetime.utcnow()
        self._grant_plan(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def verify_and_apply_webhook(
        self,
        *,
        provider: str,
        headers: Mapping[str, str],
        body: bytes,
        query: Mapping[str, str],
    ) -> PaymentOrder:
        try:
            event = self.registry.get(provider).verify_webhook(headers=headers, body=body, query=query)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{provider_display_name(provider)} webhook verification failed",
            ) from exc
        if event.status != "paid":
            self._record_payment_event(event, "ignored")
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail="Payment event accepted")
        return self._apply_paid_event(event)

    def _apply_paid_event(self, event) -> PaymentOrder:
        event_record, duplicate_order = self._record_payment_event(event, "received")
        if duplicate_order is not None:
            return duplicate_order
        try:
            order = self.mark_order_paid(
                merchant_order_id=event.merchant_order_id,
                provider=event.provider,
                provider_order_id=event.provider_order_id,
                paid_amount_cents=event.paid_amount_cents,
                currency=event.currency,
            )
        except HTTPException as exc:
            if event_record is not None:
                event_record.processing_status = "failed"
                event_record.error_message = str(exc.detail)
                self.db.commit()
            raise
        if event_record is not None:
            event_record.order_id = order.id
            event_record.processing_status = "applied"
            self.db.commit()
        return order

    def _grant_plan(self, order: PaymentOrder) -> None:
        user = self.db.query(User).filter(User.id == order.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment user not found")

        period_days = PLAN_CATALOG[order.plan]["period_days"]
        now = datetime.utcnow()
        current_end = user.subscription_end_date if user.subscription_end_date and user.subscription_end_date > now else now
        user.role = UserRole.PRO
        user.subscription_id = order.merchant_order_id
        user.subscription_status = "active"
        user.subscription_end_date = current_end + timedelta(days=period_days)

    def _ensure_provider_account(self, user: User, provider: str) -> None:
        account = self.db.query(PaymentProviderAccount).filter(
            PaymentProviderAccount.user_id == user.id,
            PaymentProviderAccount.provider == provider,
        ).first()
        if account:
            return
        self.db.add(PaymentProviderAccount(user_id=user.id, provider=provider))

    def _record_payment_event(self, event, processing_status: str | None):
        provider_event_id = event.provider_event_id or f"{event.provider}:{event.merchant_order_id}:{event.status}"
        order = self.db.query(PaymentOrder).filter(
            PaymentOrder.merchant_order_id == event.merchant_order_id,
            PaymentOrder.provider == event.provider,
        ).first()
        event_record = PaymentEvent(
            order_id=order.id if order else None,
            provider=event.provider,
            provider_event_id=provider_event_id,
            merchant_order_id=event.merchant_order_id,
            provider_order_id=event.provider_order_id,
            event_type=event.status,
            processing_status=processing_status or "received",
            amount_cents=event.paid_amount_cents,
            currency=event.currency,
            raw_summary=self._payment_event_summary(event.raw_payload),
        )
        self.db.add(event_record)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            existing_event = self.db.query(PaymentEvent).filter(
                PaymentEvent.provider == event.provider,
                PaymentEvent.provider_event_id == provider_event_id,
            ).first()
            duplicate_order = None
            if existing_event and existing_event.order_id:
                duplicate_order = self.db.query(PaymentOrder).filter(
                    PaymentOrder.id == existing_event.order_id,
                ).first()
            if duplicate_order is None and order and order.status == "paid":
                duplicate_order = order
            return existing_event, duplicate_order
        return event_record, None

    @staticmethod
    def _payment_event_summary(raw_payload: dict | None) -> str | None:
        if not raw_payload:
            return None
        safe_items = {
            key: value
            for key, value in raw_payload.items()
            if key in {"type", "status", "capture_status", "trade_status", "trade_state", "mode", "sign_type", "provider"}
        }
        if not safe_items:
            return None
        import json

        return json.dumps(safe_items, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _provider_webhook_url(provider: str) -> str:
        return (
            f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}"
            f"{settings.API_V1_PREFIX}/payment/webhooks/{provider}"
        )

    @staticmethod
    def _success_return_url(success_url: str, provider: str, merchant_order_id: str) -> str:
        separator = "&" if "?" in success_url else "?"
        return f"{success_url}{separator}provider={provider}&order_id={merchant_order_id}"
