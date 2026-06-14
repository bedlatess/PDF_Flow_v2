"""Admin payment operations and reconciliation summaries."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.payment import PaymentService
from app.domains.payment.config_store import is_managed_payment_provider, list_safe_provider_configs
from app.domains.payment.providers import PaymentProviderConfig, provider_display_name
from app.models.user import PaymentEvent, PaymentOrder, User


HOSTED_GATEWAY_PROVIDERS = {"epay", "tokenpay", "bepusdt", "epusdt", "okpay"}


def _safe_diag(value: object | None, fallback: str = "none", max_length: int = 240) -> str:
    if value is None:
        return fallback
    text = str(value).replace("\n", " ").replace("\r", " ").strip()
    if not text:
        return fallback
    if len(text) > max_length:
        return f"{text[:max_length - 3]}..."
    return text


def _serialize_payment_order(order: PaymentOrder, user_email: str | None = None) -> dict:
    return {
        "id": order.id,
        "user_id": order.user_id,
        "user_email": user_email,
        "provider": order.provider,
        "provider_display_name": provider_display_name(order.provider),
        "merchant_order_id": order.merchant_order_id,
        "provider_order_id": order.provider_order_id,
        "plan": order.plan,
        "amount_cents": order.amount_cents,
        "currency": order.currency,
        "status": order.status,
        "checkout_url_present": bool(order.checkout_url),
        "qr_code_url_present": bool(order.qr_code_url),
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "expires_at": order.expires_at,
        "paid_at": order.paid_at,
    }


def _serialize_payment_event(event: PaymentEvent) -> dict:
    return {
        "id": event.id,
        "order_id": event.order_id,
        "provider": event.provider,
        "provider_event_id": event.provider_event_id,
        "merchant_order_id": event.merchant_order_id,
        "provider_order_id": event.provider_order_id,
        "event_type": event.event_type,
        "processing_status": event.processing_status,
        "amount_cents": event.amount_cents,
        "currency": event.currency,
        "raw_summary": event.raw_summary,
        "error_message": event.error_message,
        "created_at": event.created_at,
    }


def _provider_configured(provider: str) -> bool:
    return not _payment_provider_missing_config(provider)


def _payment_webhook_url(provider: str) -> str:
    return (
        f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}"
        f"{settings.API_V1_PREFIX}/payment/webhooks/{provider}"
    )


def _payment_return_url(path: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}{path}"


def _payment_provider_required_config(provider: str) -> list[str]:
    if provider == "stripe":
        return [
            "payment_provider_configs.stripe.price_id_monthly",
            "payment_provider_configs.stripe.price_id_yearly",
            "payment_provider_configs.stripe.secret_key",
            "payment_provider_configs.stripe.webhook_secret",
        ]
    if provider == "paypal":
        return [
            "payment_provider_configs.paypal.api_base_url",
            "payment_provider_configs.paypal.client_id",
            "payment_provider_configs.paypal.client_secret",
        ]
    if provider == "alipay":
        return ["ALIPAY_APP_ID", "ALIPAY_PRIVATE_KEY", "ALIPAY_PUBLIC_KEY"]
    if provider == "wechat":
        return [
            "WECHAT_PAY_APP_ID",
            "WECHAT_PAY_MCH_ID",
            "WECHAT_PAY_SERIAL_NO",
            "WECHAT_PAY_PRIVATE_KEY",
            "WECHAT_PAY_API_V3_KEY",
            "WECHAT_PAY_PLATFORM_CERT",
        ]
    if provider in HOSTED_GATEWAY_PROVIDERS:
        return [
            f"PAYMENT_GATEWAY_CONFIGS.{provider}.merchant_id",
            f"PAYMENT_GATEWAY_CONFIGS.{provider}.secret",
            f"PAYMENT_GATEWAY_CONFIGS.{provider}.create_url",
        ]
    if provider == "gmpay":
        return [
            "payment_provider_configs.gmpay.api_base_url",
            "payment_provider_configs.gmpay.pid",
            "payment_provider_configs.gmpay.secret_key",
        ]
    return [f"PAYMENT_PROVIDER_CHECKOUT_URLS.{provider}"]


def _legacy_payment_provider_required_config(provider: str) -> list[str]:
    if provider == "stripe":
        return [
            "STRIPE_SECRET_KEY",
            "STRIPE_WEBHOOK_SECRET",
            "STRIPE_PRICE_ID_MONTHLY",
            "STRIPE_PRICE_ID_YEARLY",
        ]
    if provider == "paypal":
        return ["PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET", "PAYPAL_WEBHOOK_ID"]
    return _payment_provider_required_config(provider)


def _payment_provider_missing_config(provider: str) -> list[str]:
    gateway_config = settings.PAYMENT_GATEWAY_CONFIGS.get(provider, {})
    values = {
        "STRIPE_SECRET_KEY": settings.STRIPE_SECRET_KEY,
        "STRIPE_WEBHOOK_SECRET": settings.STRIPE_WEBHOOK_SECRET,
        "STRIPE_PRICE_ID_MONTHLY": settings.STRIPE_PRICE_ID_MONTHLY,
        "STRIPE_PRICE_ID_YEARLY": settings.STRIPE_PRICE_ID_YEARLY,
        "PAYPAL_CLIENT_ID": settings.PAYPAL_CLIENT_ID,
        "PAYPAL_CLIENT_SECRET": settings.PAYPAL_CLIENT_SECRET,
        "PAYPAL_WEBHOOK_ID": settings.PAYPAL_WEBHOOK_ID,
        "ALIPAY_APP_ID": settings.ALIPAY_APP_ID,
        "ALIPAY_PRIVATE_KEY": settings.ALIPAY_PRIVATE_KEY,
        "ALIPAY_PUBLIC_KEY": settings.ALIPAY_PUBLIC_KEY,
        "WECHAT_PAY_APP_ID": settings.WECHAT_PAY_APP_ID,
        "WECHAT_PAY_MCH_ID": settings.WECHAT_PAY_MCH_ID,
        "WECHAT_PAY_SERIAL_NO": settings.WECHAT_PAY_SERIAL_NO,
        "WECHAT_PAY_PRIVATE_KEY": settings.WECHAT_PAY_PRIVATE_KEY,
        "WECHAT_PAY_API_V3_KEY": settings.WECHAT_PAY_API_V3_KEY,
        "WECHAT_PAY_PLATFORM_CERT": settings.WECHAT_PAY_PLATFORM_CERT,
        f"PAYMENT_GATEWAY_CONFIGS.{provider}.merchant_id": gateway_config.get("merchant_id"),
        f"PAYMENT_GATEWAY_CONFIGS.{provider}.secret": gateway_config.get("secret"),
        f"PAYMENT_GATEWAY_CONFIGS.{provider}.create_url": gateway_config.get("create_url"),
        f"PAYMENT_PROVIDER_CHECKOUT_URLS.{provider}": settings.PAYMENT_PROVIDER_CHECKOUT_URLS.get(provider),
    }
    return [
        key for key in _legacy_payment_provider_required_config(provider)
        if not values.get(key)
    ]


def _payment_provider_console_hint(provider: str) -> str:
    hints = {
        "stripe": "Stripe Dashboard > Developers > Webhooks",
        "paypal": "PayPal Developer Dashboard > Apps & Credentials > Webhooks",
        "epay": "易支付商户后台 > 支付接口/异步通知地址",
        "alipay": "支付宝开放平台 > 应用信息 > 开发设置 > 授权回调/异步通知",
        "wechat": "微信支付商户平台 > 产品中心/开发配置 > 支付通知地址",
        "tokenpay": "TokenPay 管理后台 > 通知地址/回调地址",
        "bepusdt": "BEPUSDT 管理后台 > 异步通知地址",
        "epusdt": "EPUSDT 管理后台 > 异步通知地址",
        "okpay": "OKPay 商户后台 > 回调/通知地址",
        "gmpay": "GM Pay merchant console > notify URL / checkout settings",
    }
    return hints.get(provider, "Provider merchant console > webhook or notification URL")


def _payment_provider_setup_notes(provider: str) -> list[str]:
    notes = [
        "Use the webhook/notify URL as the provider server callback URL.",
        "Success and cancel URLs are user return pages only; they must not be treated as payment proof.",
        "Keep provider secrets in backend environment variables, not in frontend code.",
    ]
    if provider == "paypal":
        notes.append("After creating the PayPal webhook, copy its webhook id into PAYPAL_WEBHOOK_ID.")
    if provider == "wechat":
        notes.append("WeChat Pay notifications require API v3 key, merchant private key, and platform certificate verification.")
    if provider in HOSTED_GATEWAY_PROVIDERS:
        notes.append("If the gateway supports a custom notify_url, leave it unset to use the backend default unless the merchant console requires an override.")
    if provider == "gmpay":
        notes.append("GM Pay webhook is Phase 1 skeleton-only; do not treat return or success pages as payment proof.")
    return notes


def _payment_provider_sandbox_runbook(provider: str) -> list[str]:
    common = [
        "Enable this provider in PAYMENT_ENABLED_PROVIDERS only after required backend config is present.",
        "Create a small monthly test checkout from the Pricing page while signed in as a test account.",
        "Complete the provider sandbox payment and return to the frontend success page.",
        "Refresh this admin payment view and confirm the order becomes paid or an actionable review state.",
        "Confirm a PaymentEvent was recorded with processing_status=applied for the paid order.",
    ]
    provider_steps = {
        "paypal": [
            "Create the PayPal sandbox app webhook and copy the generated webhook id into PAYPAL_WEBHOOK_ID.",
            "After approval, call or trigger backend capture for the returned merchant order if the PayPal flow did not auto-capture.",
        ],
        "alipay": [
            "Use the Alipay sandbox gateway and sandbox buyer account for the first payment.",
            "Verify the Alipay notify payload signature and trade_success/trade_finished state are accepted.",
        ],
        "wechat": [
            "Use WeChat Pay sandbox or a low-value live test because Native pay may depend on merchant account capability.",
            "Verify API v3 notification decryption and platform signature validation before treating the order as paid.",
        ],
        "stripe": [
            "Use Stripe test card 4242 4242 4242 4242 and confirm the checkout.session.completed webhook is delivered.",
        ],
        "epay": [
            "Use the gateway's test merchant if available, otherwise run a low-value live test with a dedicated test order.",
        ],
        "tokenpay": [
            "Use a low-value token payment and wait for the gateway callback instead of trusting the return page.",
        ],
        "bepusdt": [
            "Use a low-value USDT test order and verify the gateway callback amount/currency mapping.",
        ],
        "epusdt": [
            "Use a low-value USDT test order and verify the gateway callback amount/currency mapping.",
        ],
        "okpay": [
            "Use the OKPay sandbox or a low-value live test and verify the callback signature.",
        ],
        "gmpay": [
            "Create a GM Pay checkout and confirm the returned payment_url opens the GM Pay cashier.",
            "Do not verify automatic Pro activation until a real GM Pay webhook sample is available.",
        ],
    }
    return common + provider_steps.get(provider, [])


def _payment_provider_go_live_checklist(provider: str) -> list[str]:
    checklist = [
        "BACKEND_PUBLIC_URL uses the public HTTPS backend domain that the provider can reach.",
        "FRONTEND_URL uses the public HTTPS frontend domain users will return to.",
        "Webhook/notify URL is configured in the provider dashboard exactly as shown here.",
        "Required backend config keys are present in the production environment.",
        "A real paid test order has a matching PaymentOrder and applied PaymentEvent.",
        "Duplicate webhook replay does not create duplicate entitlement time.",
        "Amount and currency mismatches remain in a review state instead of granting access.",
    ]
    if provider == "paypal":
        checklist.append("PayPal API base URL is switched from sandbox to live only after live app credentials are present.")
    if provider == "alipay":
        checklist.append("Alipay gateway URL and public/private keys match the live application.")
    if provider == "wechat":
        checklist.append("WeChat Pay merchant serial, private key, platform certificate, and API v3 key all match the live merchant.")
    if provider in HOSTED_GATEWAY_PROVIDERS:
        checklist.append("Gateway create_url, merchant id, secret, and sign_type match the live gateway documentation.")
    if provider == "gmpay":
        checklist.append("GM Pay webhook sample, signature verification, amount/currency checks, and idempotency are implemented before entitlement automation.")
    return checklist


def _payment_provider_expected_event_flow(provider: str) -> list[str]:
    if provider == "paypal":
        return [
            "checkout_created -> provider approval page",
            "buyer approves payment",
            "backend capture confirms COMPLETED",
            "PaymentEvent processing_status=applied",
            "PaymentOrder status=paid and entitlement extended once",
        ]
    if provider == "stripe":
        return [
            "checkout_created -> Stripe Checkout",
            "checkout.session.completed webhook received",
            "PaymentEvent processing_status=applied",
            "PaymentOrder status=paid and entitlement/subscription state updated once",
        ]
    if provider == "gmpay":
        return [
            "checkout_created -> GM Pay cashier payment_url",
            "GM Pay webhook endpoint receives callbacks",
            "Phase 1 records callbacks without marking orders paid",
            "Entitlement remains unchanged until strict webhook verification is implemented",
        ]
    if provider in {"alipay", "wechat", *HOSTED_GATEWAY_PROVIDERS}:
        return [
            "checkout_created -> provider hosted/QR payment page",
            "provider asynchronous notify/webhook received by backend",
            "signature, merchant order id, amount, and currency validated",
            "PaymentEvent processing_status=applied",
            "PaymentOrder status=paid and entitlement extended once",
        ]
    return [
        "checkout_created",
        "provider callback received",
        "PaymentEvent processing_status=applied",
        "PaymentOrder status=paid",
    ]


def _payment_provider_troubleshooting_steps(provider: str) -> list[str]:
    steps = [
        "If no PaymentEvent appears, check provider dashboard delivery logs and BACKEND_PUBLIC_URL reachability.",
        "If verification fails, compare configured secret/certificate/public key with the provider dashboard.",
        "If amount_mismatch or currency_mismatch appears, compare plan pricing, provider currency, and minor-unit conversion.",
        "If checkout opens but never activates Pro, remember the frontend return page is not payment proof; inspect the webhook event.",
        "If the same webhook is delivered repeatedly, confirm provider_event_id stays stable and entitlement is not extended twice.",
    ]
    if provider == "wechat":
        steps.append("For WeChat Pay decrypt failures, verify API v3 key length and platform certificate freshness.")
    if provider == "paypal":
        steps.append("For PayPal webhook failures, confirm PAYPAL_WEBHOOK_ID belongs to the same app as PAYPAL_CLIENT_ID.")
    if provider in HOSTED_GATEWAY_PROVIDERS:
        steps.append("For hosted gateway failures, verify sign_type and parameter ordering against the gateway documentation.")
    if provider == "gmpay":
        steps.append("For GM Pay, collect the real webhook sample before enabling paid status or Pro entitlement automation.")
    return steps


def _payment_provider_evidence_fields(provider: str) -> list[str]:
    fields = [
        "provider",
        "merchant_order_id",
        "provider_order_id",
        "provider_event_id",
        "amount_cents",
        "currency",
        "PaymentOrder.status",
        "PaymentEvent.processing_status",
        "paid_at",
        "current_period_end",
    ]
    if provider == "paypal":
        fields.extend(["PayPal capture id", "PayPal webhook id"])
    if provider == "wechat":
        fields.extend(["Wechat transaction_id", "Wechat out_trade_no", "Wechat trade_state"])
    if provider == "alipay":
        fields.extend(["Alipay trade_no", "Alipay out_trade_no", "Alipay trade_status"])
    if provider in HOSTED_GATEWAY_PROVIDERS:
        fields.extend(["gateway trade id", "gateway sign_type", "gateway callback timestamp"])
    if provider == "gmpay":
        fields.extend(["GM Pay trade_id", "GM Pay payment_url", "webhook sample reference"])
    return fields


def _payment_status_tone(status_value: str) -> str:
    if status_value == "paid":
        return "settled"
    if status_value in {"amount_mismatch", "currency_mismatch"}:
        return "needs_review"
    if status_value in {"failed", "canceled", "cancelled"}:
        return "failed"
    return "open"


def _payment_provider_acceptance_state(
    option,
    configured: bool,
    missing_config_keys: list[str],
    provider_orders: list[PaymentOrder],
    provider_events: list[PaymentEvent],
) -> dict:
    applied_events = [
        event for event in provider_events
        if event.processing_status == "applied"
    ]
    failed_events = [
        event for event in provider_events
        if event.processing_status == "failed"
    ]
    paid_orders = [order for order in provider_orders if order.status == "paid"]
    review_orders = [
        order for order in provider_orders
        if _payment_status_tone(order.status) == "needs_review"
    ]
    pending_orders = [order for order in provider_orders if order.status == "pending"]
    latest_paid_event = max(applied_events, key=lambda item: item.created_at) if applied_events else None

    blockers: list[str] = []
    if not option.enabled:
        blockers.append("Provider is not enabled in PAYMENT_ENABLED_PROVIDERS.")
        return {
            "acceptance_status": "disabled",
            "acceptance_label": "Disabled",
            "acceptance_detail": "Provider is not visible in checkout yet.",
            "acceptance_blockers": blockers,
            "latest_paid_event_at": None,
        }

    if not configured:
        blockers.extend(missing_config_keys or ["Required merchant configuration is missing."])
        return {
            "acceptance_status": "missing_config",
            "acceptance_label": "Missing config",
            "acceptance_detail": "Add backend merchant config before starting sandbox or live smoke tests.",
            "acceptance_blockers": blockers,
            "latest_paid_event_at": None,
        }

    if review_orders or failed_events:
        if review_orders:
            blockers.append("At least one order is in a manual review state.")
        if failed_events:
            blockers.append("At least one payment event failed processing.")
        return {
            "acceptance_status": "needs_review",
            "acceptance_label": "Needs review",
            "acceptance_detail": "Configuration exists, but a payment order or callback needs manual reconciliation.",
            "acceptance_blockers": blockers,
            "latest_paid_event_at": latest_paid_event.created_at if latest_paid_event else None,
        }

    if paid_orders and applied_events:
        return {
            "acceptance_status": "accepted",
            "acceptance_label": "Smoke passed",
            "acceptance_detail": "At least one paid order has a matching applied PaymentEvent.",
            "acceptance_blockers": [],
            "latest_paid_event_at": latest_paid_event.created_at if latest_paid_event else None,
        }

    if pending_orders:
        blockers.append("A checkout exists but no applied provider event has arrived yet.")
        return {
            "acceptance_status": "waiting_callback",
            "acceptance_label": "Waiting callback",
            "acceptance_detail": "A test order exists; finish payment or inspect provider callback delivery.",
            "acceptance_blockers": blockers,
            "latest_paid_event_at": None,
        }

    blockers.append("No test order has been created for this provider yet.")
    return {
        "acceptance_status": "ready_to_test",
        "acceptance_label": "Ready to test",
        "acceptance_detail": "Configuration is present; create a sandbox or low-value live order from Pricing.",
        "acceptance_blockers": blockers,
        "latest_paid_event_at": None,
    }


def _build_payment_reconciliation_summary(
    generated_at: datetime,
    orders: list[PaymentOrder],
    events: list[PaymentEvent],
    provider_rows: list[dict],
    expired_pending_orders: int,
) -> str:
    latest = orders[0] if orders else None
    latest_event = max(events, key=lambda item: item.created_at) if events else None
    provider_status = ", ".join(
        f"{item['key']}={'configured' if item['configured'] else 'missing_config'}"
        for item in provider_rows
        if item["enabled"]
    ) or "none"
    paid_amount = sum(order.amount_cents for order in orders if order.status == "paid")
    review_orders = [
        order for order in orders
        if _payment_status_tone(order.status) == "needs_review"
    ]

    lines = [
        "PDF-Flow payment reconciliation packet",
        f"Generated: {generated_at.isoformat()}Z",
        f"Environment: {settings.ENVIRONMENT}",
        f"Orders: total={len(orders)}, paid={len([order for order in orders if order.status == 'paid'])}, pending={len([order for order in orders if order.status == 'pending'])}, expired_pending={expired_pending_orders}, needs_review={len(review_orders)}",
        f"Events: total={len(events)}, applied={len([event for event in events if event.processing_status == 'applied'])}, failed={len([event for event in events if event.processing_status == 'failed'])}, ignored={len([event for event in events if event.processing_status == 'ignored'])}",
        f"Paid amount cents: {paid_amount}",
        f"Provider config: {provider_status}",
    ]

    if latest:
        lines.extend([
            "",
            "Latest order:",
            f"- merchant_order_id={_safe_diag(latest.merchant_order_id)}",
            f"- provider={_safe_diag(latest.provider)}, status={_safe_diag(latest.status)}, plan={_safe_diag(latest.plan)}",
            f"- amount={latest.amount_cents} {latest.currency}",
            f"- user_id={latest.user_id}, provider_order_id={_safe_diag(latest.provider_order_id)}",
        ])

    if latest_event:
        lines.extend([
            "",
            "Latest payment event:",
            f"- provider_event_id={_safe_diag(latest_event.provider_event_id)}",
            f"- provider={_safe_diag(latest_event.provider)}, status={_safe_diag(latest_event.processing_status)}, type={_safe_diag(latest_event.event_type)}",
            f"- merchant_order_id={_safe_diag(latest_event.merchant_order_id)}",
        ])

    if review_orders:
        review = review_orders[0]
        lines.extend([
            "",
            "First order needing review:",
            f"- merchant_order_id={_safe_diag(review.merchant_order_id)}",
            f"- provider={_safe_diag(review.provider)}, status={_safe_diag(review.status)}",
            f"- amount={review.amount_cents} {review.currency}",
        ])

    lines.extend([
        "",
        "Privacy note: provider raw payloads, document contents, and checkout URLs are not included.",
    ])
    return "\n".join(lines)


def _build_payment_integration_evidence_packet(
    generated_at: datetime,
    orders: list[PaymentOrder],
    events: list[PaymentEvent],
    provider_rows: list[dict],
) -> str:
    lines = [
        "PDF-Flow payment integration evidence packet",
        f"Generated: {generated_at.isoformat()}Z",
        f"Environment: {settings.ENVIRONMENT}",
        f"Backend public URL: {_safe_diag(settings.BACKEND_PUBLIC_URL, max_length=180)}",
        f"Frontend URL: {_safe_diag(settings.FRONTEND_URL, max_length=180)}",
        "",
        "Manual test fields to fill:",
        "- tester=",
        "- provider_dashboard_event_url=",
        "- sandbox_or_live=",
        "- provider_dashboard_status=",
        "- screenshot_or_ticket_ref=",
    ]

    for provider_row in provider_rows:
        provider_key = provider_row["key"]
        provider_orders = [order for order in orders if order.provider == provider_key]
        provider_events = [event for event in events if event.provider == provider_key]
        latest_order = max(provider_orders, key=lambda item: item.created_at) if provider_orders else None
        latest_event = max(provider_events, key=lambda item: item.created_at) if provider_events else None

        lines.extend([
            "",
            f"Provider: {provider_row['display_name']} ({provider_key})",
            f"- enabled={provider_row['enabled']}, configured={provider_row['configured']}, settlement={_safe_diag(provider_row.get('settlement'))}",
            f"- acceptance_status={_safe_diag(provider_row.get('acceptance_status'))}, label={_safe_diag(provider_row.get('acceptance_label'))}",
            f"- acceptance_detail={_safe_diag(provider_row.get('acceptance_detail'), max_length=220)}",
            f"- acceptance_blockers={'; '.join(provider_row.get('acceptance_blockers') or []) or 'none'}",
            f"- webhook_url={_safe_diag(provider_row.get('webhook_url'), max_length=220)}",
            f"- success_return_url={_safe_diag(provider_row.get('success_return_url'), max_length=220)}",
            f"- cancel_return_url={_safe_diag(provider_row.get('cancel_return_url'), max_length=220)}",
            f"- missing_config={', '.join(provider_row.get('missing_config_keys') or []) or 'none'}",
        ])

        if latest_order:
            lines.extend([
                "- latest_order:",
                f"  merchant_order_id={_safe_diag(latest_order.merchant_order_id)}",
                f"  provider_order_id={_safe_diag(latest_order.provider_order_id)}",
                f"  status={_safe_diag(latest_order.status)}, amount={latest_order.amount_cents} {latest_order.currency}",
                f"  paid_at={latest_order.paid_at.isoformat() if latest_order.paid_at else 'none'}",
            ])
        else:
            lines.append("- latest_order=none")

        if latest_event:
            lines.extend([
                "- latest_event:",
                f"  provider_event_id={_safe_diag(latest_event.provider_event_id)}",
                f"  type={_safe_diag(latest_event.event_type)}, processing_status={_safe_diag(latest_event.processing_status)}",
                f"  amount={latest_event.amount_cents if latest_event.amount_cents is not None else 'none'} {latest_event.currency or ''}".rstrip(),
                f"  error={_safe_diag(latest_event.error_message)}",
            ])
        else:
            lines.append("- latest_event=none")

        lines.extend([
            "- expected_event_flow:",
            *[f"  {index + 1}. {_safe_diag(step, max_length=220)}" for index, step in enumerate(provider_row.get("expected_event_flow") or [])],
            "- evidence_fields:",
            f"  {', '.join(provider_row.get('evidence_fields') or []) or 'none'}",
            "- troubleshooting_first_steps:",
            *[f"  {index + 1}. {_safe_diag(step, max_length=220)}" for index, step in enumerate((provider_row.get("troubleshooting_steps") or [])[:3])],
        ])

    lines.extend([
        "",
        "Privacy note: checkout URLs, raw provider payloads, document contents, and secrets are not included.",
    ])
    return "\n".join(lines)


def get_payment_operations_summary(
    db: Session,
    *,
    provider: str | None = None,
    status_filter: str | None = None,
    limit: int = 50,
) -> dict:
    safe_limit = min(max(limit, 1), 100)
    service = PaymentService(db)
    provider_options = service.list_providers()
    managed_config_rows = {
        item["provider_key"]: item
        for item in list_safe_provider_configs(db)
    }
    existing_provider_keys = {option.key for option in provider_options}
    for provider_key, safe_config in managed_config_rows.items():
        if provider_key not in existing_provider_keys:
            provider_options.append(PaymentProviderConfig(
                key=provider_key,
                enabled=bool(safe_config["enabled"] and safe_config["configured"]),
                display_name=safe_config["display_name"],
                settlement="one_time_entitlement",
                supports_subscription=False,
                supports_one_time=True,
            ))

    query = db.query(PaymentOrder, User.email).outerjoin(User, PaymentOrder.user_id == User.id)
    if provider:
        query = query.filter(PaymentOrder.provider == provider)
    if status_filter:
        query = query.filter(PaymentOrder.status == status_filter)

    recent_rows = (
        query
        .order_by(PaymentOrder.created_at.desc())
        .limit(safe_limit)
        .all()
    )
    recent_orders = [
        _serialize_payment_order(order, user_email=email)
        for order, email in recent_rows
    ]
    recent_events = (
        db.query(PaymentEvent)
        .order_by(PaymentEvent.created_at.desc())
        .limit(safe_limit)
        .all()
    )

    all_orders = db.query(PaymentOrder).order_by(PaymentOrder.created_at.desc()).all()
    all_events = db.query(PaymentEvent).all()
    generated_at = datetime.utcnow()
    pending_orders = [order for order in all_orders if order.status == "pending"]
    paid_orders = [order for order in all_orders if order.status == "paid"]
    failed_orders = [
        order for order in all_orders
        if order.status in {"failed", "canceled", "cancelled"}
    ]
    amount_mismatch_orders = [order for order in all_orders if order.status == "amount_mismatch"]
    currency_mismatch_orders = [order for order in all_orders if order.status == "currency_mismatch"]
    expired_pending_orders = [
        order for order in pending_orders
        if order.expires_at is not None and order.expires_at < generated_at
    ]
    currency_breakdown: dict[str, int] = {}
    for order in paid_orders:
        currency = (order.currency or "UNKNOWN").upper()
        currency_breakdown[currency] = currency_breakdown.get(currency, 0) + order.amount_cents

    provider_rows = []
    for option in provider_options:
        provider_orders = [order for order in all_orders if order.provider == option.key]
        provider_events = [event for event in all_events if event.provider == option.key]
        latest_order = max(provider_orders, key=lambda item: item.created_at) if provider_orders else None
        managed_row = managed_config_rows.get(option.key)
        if managed_row and managed_row["enabled"]:
            configured = bool(managed_row["configured"])
            missing_config_keys = list(managed_row["missing_config_keys"])
        else:
            configured = _provider_configured(option.key)
            missing_config_keys = _payment_provider_missing_config(option.key)
        required_config_keys = (
            _payment_provider_required_config(option.key)
            if managed_row and managed_row["enabled"] and is_managed_payment_provider(option.key)
            else _legacy_payment_provider_required_config(option.key)
        )
        acceptance_state = _payment_provider_acceptance_state(
            option,
            configured,
            missing_config_keys,
            provider_orders,
            provider_events,
        )
        if option.enabled and configured:
            detail = "Enabled and configuration is present."
        elif option.enabled:
            detail = "Enabled but merchant configuration is incomplete."
        else:
            detail = "Disabled in PAYMENT_ENABLED_PROVIDERS."
        provider_rows.append({
            "key": option.key,
            "display_name": option.display_name,
            "enabled": option.enabled,
            "configured": configured,
            **acceptance_state,
            "settlement": option.settlement,
            "supports_subscription": option.supports_subscription,
            "supports_one_time": option.supports_one_time,
            "open_orders": len([order for order in provider_orders if order.status == "pending"]),
            "paid_orders": len([order for order in provider_orders if order.status == "paid"]),
            "failed_orders": len([
                order for order in provider_orders
                if _payment_status_tone(order.status) in {"failed", "needs_review"}
            ]),
            "latest_order_at": latest_order.created_at if latest_order else None,
            "detail": detail,
            "webhook_url": _payment_webhook_url(option.key),
            "success_return_url": _payment_return_url("/payment/success"),
            "cancel_return_url": _payment_return_url("/payment/cancel"),
            "merchant_console_hint": _payment_provider_console_hint(option.key),
            "required_config_keys": required_config_keys,
            "missing_config_keys": missing_config_keys,
            "setup_notes": _payment_provider_setup_notes(option.key),
            "sandbox_runbook": _payment_provider_sandbox_runbook(option.key),
            "go_live_checklist": _payment_provider_go_live_checklist(option.key),
            "expected_event_flow": _payment_provider_expected_event_flow(option.key),
            "troubleshooting_steps": _payment_provider_troubleshooting_steps(option.key),
            "evidence_fields": _payment_provider_evidence_fields(option.key),
        })

    return {
        "generated_at": generated_at,
        "total_orders": len(all_orders),
        "pending_orders": len(pending_orders),
        "paid_orders": len(paid_orders),
        "failed_orders": len(failed_orders),
        "amount_mismatch_orders": len(amount_mismatch_orders),
        "currency_mismatch_orders": len(currency_mismatch_orders),
        "expired_pending_orders": len(expired_pending_orders),
        "paid_amount_cents": sum(order.amount_cents for order in paid_orders),
        "currency_breakdown": currency_breakdown,
        "providers": provider_rows,
        "recent_orders": recent_orders,
        "recent_events": [_serialize_payment_event(event) for event in recent_events],
        "reconciliation_summary": _build_payment_reconciliation_summary(
            generated_at,
            all_orders,
            all_events,
            provider_rows,
            len(expired_pending_orders),
        ),
        "integration_evidence_packet": _build_payment_integration_evidence_packet(
            generated_at,
            all_orders,
            all_events,
            provider_rows,
        ),
    }
