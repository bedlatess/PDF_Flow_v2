"""Admin-managed payment provider configuration storage."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import PaymentProviderConfig as PaymentProviderConfigModel


SENSITIVE_FIELD_MARKERS = (
    "secret",
    "private",
    "token",
    "certificate",
    "cert",
    "key",
)


@dataclass(frozen=True)
class PaymentProviderFieldDefinition:
    key: str
    label: str
    input_type: str = "text"
    required: bool = False
    secret: bool = False
    placeholder: str = ""
    help_text: str = ""
    min_value: int | None = None
    max_value: int | None = None


@dataclass(frozen=True)
class ManagedProviderDefinition:
    key: str
    display_name: str
    description: str
    public_defaults: dict[str, Any]
    public_fields: tuple[PaymentProviderFieldDefinition, ...]
    secret_fields: tuple[PaymentProviderFieldDefinition, ...]
    settlement: str
    supports_subscription: bool = False
    supports_one_time: bool = True
    merchant_console_hint: str = ""
    setup_notes: tuple[str, ...] = ()
    validation_checks: tuple[str, ...] = ()

    @property
    def required_public_fields(self) -> tuple[str, ...]:
        return tuple(field.key for field in self.public_fields if field.required)

    @property
    def secret_field_keys(self) -> tuple[str, ...]:
        return tuple(field.key for field in self.secret_fields)

    @property
    def required_secret_fields(self) -> tuple[str, ...]:
        return tuple(field.key for field in self.secret_fields if field.required)


GMPAY_DEFAULT_PUBLIC_CONFIG: dict[str, Any] = {
    "api_base_url": "",
    "pid": "",
    "currency": "cny",
    "token": "usdt",
    "network": "tron",
    "monthly_amount_cents": 990,
    "yearly_amount_cents": 7900,
    "order_ttl_minutes": 30,
    "return_url": "",
}


STRIPE_DEFAULT_PUBLIC_CONFIG: dict[str, Any] = {
    "price_id_monthly": "",
    "price_id_yearly": "",
}


PAYPAL_DEFAULT_PUBLIC_CONFIG: dict[str, Any] = {
    "api_base_url": "https://api-m.sandbox.paypal.com",
    "client_id": "",
    "webhook_id": "",
}


MANAGED_PAYMENT_PROVIDERS: dict[str, ManagedProviderDefinition] = {
    "stripe": ManagedProviderDefinition(
        key="stripe",
        display_name="Stripe",
        description=(
            "Hosted Stripe Checkout sessions. Payment proof still comes from "
            "verified Stripe webhooks, not the frontend success page."
        ),
        public_defaults=STRIPE_DEFAULT_PUBLIC_CONFIG,
        public_fields=(
            PaymentProviderFieldDefinition(
                key="price_id_monthly",
                label="Monthly Price ID",
                required=True,
                placeholder="price_...",
                help_text="Stripe recurring price used for monthly Pro checkout.",
            ),
            PaymentProviderFieldDefinition(
                key="price_id_yearly",
                label="Yearly Price ID",
                required=True,
                placeholder="price_...",
                help_text="Stripe recurring price used for annual Pro checkout.",
            ),
        ),
        secret_fields=(
            PaymentProviderFieldDefinition(
                key="secret_key",
                label="Secret Key",
                input_type="password",
                required=True,
                secret=True,
                placeholder="Leave blank to keep existing",
                help_text="Write-only Stripe API secret. It is encrypted at rest and never returned.",
            ),
            PaymentProviderFieldDefinition(
                key="webhook_secret",
                label="Webhook Secret",
                input_type="password",
                required=True,
                secret=True,
                placeholder="Leave blank to keep existing",
                help_text="Write-only endpoint signing secret for Stripe webhooks.",
            ),
        ),
        settlement="subscription",
        supports_subscription=True,
        merchant_console_hint="Stripe Dashboard > Developers > Webhooks",
        setup_notes=(
            "Use the webhook URL shown here as the Stripe endpoint URL.",
            "Success and cancel URLs are user return pages only; they are not payment proof.",
            "Use Stripe test mode first, then switch to live keys and live price ids together.",
        ),
        validation_checks=("required_fields", "stripe_checkout_schema"),
    ),
    "paypal": ManagedProviderDefinition(
        key="paypal",
        display_name="PayPal",
        description=(
            "PayPal checkout order creation and approval URL handoff. Capture/webhook "
            "entitlement hardening remains outside this phase."
        ),
        public_defaults=PAYPAL_DEFAULT_PUBLIC_CONFIG,
        public_fields=(
            PaymentProviderFieldDefinition(
                key="api_base_url",
                label="API Base URL",
                input_type="url",
                required=True,
                placeholder="https://api-m.sandbox.paypal.com",
                help_text="Use sandbox for testing and live API only after live credentials are ready.",
            ),
            PaymentProviderFieldDefinition(
                key="client_id",
                label="Client ID",
                required=True,
                help_text="PayPal REST app client id.",
            ),
            PaymentProviderFieldDefinition(
                key="webhook_id",
                label="Webhook ID",
                required=False,
                help_text="Needed for strict webhook verification; optional for checkout URL creation.",
            ),
        ),
        secret_fields=(
            PaymentProviderFieldDefinition(
                key="client_secret",
                label="Client Secret",
                input_type="password",
                required=True,
                secret=True,
                placeholder="Leave blank to keep existing",
                help_text="Write-only PayPal REST app secret.",
            ),
        ),
        settlement="one_time_entitlement",
        merchant_console_hint="PayPal Developer Dashboard > Apps & Credentials > Webhooks",
        setup_notes=(
            "Create the PayPal webhook from the same REST app as the client id.",
            "Copy the webhook id when strict webhook verification is enabled.",
            "Keep sandbox and live credentials separated.",
        ),
        validation_checks=("required_fields", "paypal_checkout_schema"),
    ),
    "gmpay": ManagedProviderDefinition(
        key="gmpay",
        display_name="GM Pay",
        description=(
            "GM Pay hosted cashier integration. Webhook is skeleton-only until real "
            "callback samples are verified."
        ),
        public_defaults=GMPAY_DEFAULT_PUBLIC_CONFIG,
        public_fields=(
            PaymentProviderFieldDefinition(
                key="api_base_url",
                label="API Base URL",
                input_type="url",
                required=True,
                placeholder="https://pay.example.com",
                help_text="GM Pay API origin without a trailing slash.",
            ),
            PaymentProviderFieldDefinition(
                key="pid",
                label="PID / Merchant ID",
                required=True,
                help_text="Merchant identifier issued by GM Pay.",
            ),
            PaymentProviderFieldDefinition(
                key="currency",
                label="Currency",
                required=True,
                placeholder="cny",
            ),
            PaymentProviderFieldDefinition(
                key="token",
                label="Token",
                required=True,
                placeholder="usdt",
            ),
            PaymentProviderFieldDefinition(
                key="network",
                label="Network",
                required=True,
                placeholder="tron",
            ),
            PaymentProviderFieldDefinition(
                key="monthly_amount_cents",
                label="Monthly Amount Cents",
                input_type="number",
                required=True,
                min_value=1,
            ),
            PaymentProviderFieldDefinition(
                key="yearly_amount_cents",
                label="Yearly Amount Cents",
                input_type="number",
                required=True,
                min_value=1,
            ),
            PaymentProviderFieldDefinition(
                key="order_ttl_minutes",
                label="Order TTL Minutes",
                input_type="number",
                min_value=5,
            ),
            PaymentProviderFieldDefinition(
                key="return_url",
                label="Return URL Override",
                input_type="url",
                placeholder="Optional",
            ),
        ),
        secret_fields=(
            PaymentProviderFieldDefinition(
                key="secret_key",
                label="Secret Key",
                input_type="password",
                required=True,
                secret=True,
                placeholder="Leave blank to keep existing",
                help_text="Write-only GM Pay signing secret.",
            ),
        ),
        settlement="one_time_entitlement",
        merchant_console_hint="GM Pay merchant console > notify URL / checkout settings",
        setup_notes=(
            "Create checkout first and confirm GM Pay returns a cashier payment_url.",
            "Do not use frontend success pages as payment proof.",
            "Keep automatic Pro activation disabled until strict webhook verification is implemented.",
        ),
        validation_checks=("required_fields", "local_signature_generation"),
    )
}


def is_managed_payment_provider(provider_key: str) -> bool:
    return provider_key in MANAGED_PAYMENT_PROVIDERS


def list_managed_payment_provider_keys() -> list[str]:
    return list(MANAGED_PAYMENT_PROVIDERS)


def get_managed_provider_definition(provider_key: str) -> ManagedProviderDefinition:
    try:
        return MANAGED_PAYMENT_PROVIDERS[provider_key]
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Managed payment provider not found",
        ) from exc


def _is_production() -> bool:
    return settings.ENVIRONMENT.lower() in {"prod", "production"}


def _encryption_key_material() -> str | None:
    value = (settings.PAYMENT_CONFIG_ENCRYPTION_KEY or "").strip()
    return value or None


def _require_encryption_key() -> str:
    key = _encryption_key_material()
    if key:
        return key
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="PAYMENT_CONFIG_ENCRYPTION_KEY is required for sensitive payment configuration",
    )


def payment_config_encryption_available() -> bool:
    return bool(_encryption_key_material())


def _aesgcm() -> AESGCM:
    key = hashlib.sha256(_require_encryption_key().encode("utf-8")).digest()
    return AESGCM(key)


def _encrypt_secret_payload(secrets: dict[str, str]) -> str:
    nonce = os.urandom(12)
    plaintext = json.dumps(secrets, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ciphertext = _aesgcm().encrypt(nonce, plaintext, None)
    return json.dumps(
        {
            "v": 1,
            "alg": "AESGCM-SHA256",
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        },
        sort_keys=True,
    )


def _decrypt_secret_payload(encrypted_secret_json: str | None) -> dict[str, str]:
    if not encrypted_secret_json:
        return {}
    if not payment_config_encryption_available():
        if _is_production():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="PAYMENT_CONFIG_ENCRYPTION_KEY is required to read sensitive payment configuration",
            )
        return {}
    try:
        envelope = json.loads(encrypted_secret_json)
        nonce = base64.b64decode(envelope["nonce"])
        ciphertext = base64.b64decode(envelope["ciphertext"])
        plaintext = _aesgcm().decrypt(nonce, ciphertext, None)
        data = json.loads(plaintext.decode("utf-8"))
        return {str(key): str(value) for key, value in data.items() if str(value)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment provider secrets could not be decrypted",
        ) from exc


def _load_json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return dict(parsed) if isinstance(parsed, dict) else {}


def _fingerprints(secrets: dict[str, str]) -> dict[str, dict[str, str | bool]]:
    return {
        field: {
            "configured": bool(value),
            "tail": value[-4:] if value else "",
        }
        for field, value in secrets.items()
    }


def _field_to_metadata(field: PaymentProviderFieldDefinition) -> dict[str, Any]:
    return {
        "key": field.key,
        "label": field.label,
        "input_type": field.input_type,
        "required": field.required,
        "secret": field.secret,
        "placeholder": field.placeholder,
        "help_text": field.help_text,
        "min_value": field.min_value,
        "max_value": field.max_value,
    }


def _provider_metadata(definition: ManagedProviderDefinition) -> dict[str, Any]:
    return {
        "provider_key": definition.key,
        "display_name": definition.display_name,
        "description": definition.description,
        "settlement": definition.settlement,
        "supports_subscription": definition.supports_subscription,
        "supports_one_time": definition.supports_one_time,
        "merchant_console_hint": definition.merchant_console_hint,
        "setup_notes": list(definition.setup_notes),
        "validation_checks": list(definition.validation_checks),
        "fields": {
            "public": [_field_to_metadata(field) for field in definition.public_fields],
            "secret": [_field_to_metadata(field) for field in definition.secret_fields],
        },
    }


def _secret_status(definition: ManagedProviderDefinition, row: PaymentProviderConfigModel | None) -> dict[str, dict[str, str | bool]]:
    fingerprint = _load_json_object(row.secret_fingerprint_json if row else None)
    status_map: dict[str, dict[str, str | bool]] = {}
    for field in definition.secret_field_keys:
        item = fingerprint.get(field) or {}
        configured = bool(item.get("configured"))
        tail = str(item.get("tail") or "")
        status_map[field] = {
            "configured": configured,
            "tail": tail if configured else "",
        }
    return status_map


def _merged_public_config(definition: ManagedProviderDefinition, row: PaymentProviderConfigModel | None) -> dict[str, Any]:
    config = dict(definition.public_defaults)
    config.update(_load_json_object(row.public_config_json if row else None))
    return config


def _normalize_public_config(definition: ManagedProviderDefinition, public_config: dict[str, Any] | None) -> dict[str, Any]:
    data = dict(definition.public_defaults)
    for key, value in (public_config or {}).items():
        if key not in definition.public_defaults:
            continue
        if key in {"monthly_amount_cents", "yearly_amount_cents", "order_ttl_minutes"}:
            data[key] = int(value or 0)
            continue
        text = str(value or "").strip()
        data[key] = text.rstrip("/") if key == "api_base_url" else text
    return data


def _is_public_config_complete(definition: ManagedProviderDefinition, public_config: dict[str, Any]) -> bool:
    for field in definition.required_public_fields:
        value = public_config.get(field)
        if value is None or value == "":
            return False
        if field.endswith("_amount_cents") and int(value) <= 0:
            return False
    return True


def get_payment_provider_config_row(
    db: Session,
    provider_key: str,
) -> PaymentProviderConfigModel | None:
    return db.query(PaymentProviderConfigModel).filter(
        PaymentProviderConfigModel.provider_key == provider_key,
    ).first()


def get_provider_runtime_config(db: Session, provider_key: str) -> dict[str, Any] | None:
    definition = MANAGED_PAYMENT_PROVIDERS.get(provider_key)
    if not definition:
        return None
    row = get_payment_provider_config_row(db, provider_key)
    if not row or not row.enabled:
        return None
    public_config = _merged_public_config(definition, row)
    secret_status = _secret_status(definition, row)
    if not _is_public_config_complete(definition, public_config):
        return None
    if not all(secret_status[field]["configured"] for field in definition.required_secret_fields):
        return None
    secrets = _decrypt_secret_payload(row.encrypted_secret_json)
    if not all(secrets.get(field) for field in definition.required_secret_fields):
        return None
    return {
        "provider_key": provider_key,
        "display_name": row.display_name or definition.display_name,
        "enabled": row.enabled,
        "public_config": public_config,
        "secrets": secrets,
    }


def build_safe_provider_config(
    db: Session,
    provider_key: str,
) -> dict[str, Any]:
    definition = get_managed_provider_definition(provider_key)
    row = get_payment_provider_config_row(db, provider_key)
    public_config = _merged_public_config(definition, row)
    secret_status = _secret_status(definition, row)
    missing_public = [
        field for field in definition.required_public_fields
        if public_config.get(field) in {None, ""} or (
            field.endswith("_amount_cents") and int(public_config.get(field) or 0) <= 0
        )
    ]
    missing_secret = [
        field for field in definition.required_secret_fields
        if not secret_status[field]["configured"]
    ]
    readiness_status = "ready" if not missing_public and not missing_secret else "missing_config"
    return {
        "provider_key": definition.key,
        "display_name": row.display_name if row else definition.display_name,
        "enabled": bool(row.enabled) if row else False,
        "configured": not missing_public and not missing_secret,
        "public_config": public_config,
        "secret_fields": secret_status,
        "required_public_fields": list(definition.required_public_fields),
        "required_secret_fields": list(definition.required_secret_fields),
        "missing_config_keys": missing_public + missing_secret,
        "webhook_url": (
            f"{settings.BACKEND_PUBLIC_URL.rstrip('/')}"
            f"{settings.API_V1_PREFIX}/payment/webhooks/{definition.key}"
        ),
        "updated_at": row.updated_at if row else None,
        "encryption_available": payment_config_encryption_available(),
        "webhook_status": "skeleton_no_entitlement",
        "metadata": _provider_metadata(definition),
        "readiness": {
            "status": readiness_status,
            "label": "Ready" if readiness_status == "ready" else "Missing config",
            "detail": (
                "Required public fields and write-only secrets are configured."
                if readiness_status == "ready"
                else "Required public fields or write-only secrets are missing."
            ),
            "missing_config_keys": missing_public + missing_secret,
            "validation_checks": list(definition.validation_checks),
        },
    }


def list_safe_provider_configs(db: Session) -> list[dict[str, Any]]:
    return [
        build_safe_provider_config(db, provider_key)
        for provider_key in list_managed_payment_provider_keys()
    ]


def update_provider_config(
    db: Session,
    *,
    provider_key: str,
    enabled: bool,
    public_config: dict[str, Any] | None,
    secret_values: dict[str, str] | None,
    admin_user_id: int,
) -> tuple[dict[str, Any], list[str]]:
    definition = get_managed_provider_definition(provider_key)
    row = get_payment_provider_config_row(db, provider_key)
    if row is None:
        row = PaymentProviderConfigModel(
            provider_key=definition.key,
            display_name=definition.display_name,
            enabled=False,
            public_config_json=json.dumps(definition.public_defaults, sort_keys=True),
        )
        db.add(row)
        db.flush()

    normalized_public = _normalize_public_config(definition, public_config)
    existing_secrets = _decrypt_secret_payload(row.encrypted_secret_json)
    changed_fields: list[str] = []
    previous_public = _load_json_object(row.public_config_json)
    for field, value in normalized_public.items():
        if previous_public.get(field) != value:
            changed_fields.append(field)

    merged_secrets = dict(existing_secrets)
    incoming_secrets = {
        key: str(value).strip()
        for key, value in (secret_values or {}).items()
        if key in definition.secret_field_keys and str(value or "").strip()
    }
    if incoming_secrets and not payment_config_encryption_available() and _is_production():
        _require_encryption_key()
    for field, value in incoming_secrets.items():
        if merged_secrets.get(field) != value:
            changed_fields.append(field)
        merged_secrets[field] = value

    if incoming_secrets:
        row.encrypted_secret_json = _encrypt_secret_payload(merged_secrets)
        row.secret_fingerprint_json = json.dumps(_fingerprints(merged_secrets), sort_keys=True)
    elif row.encrypted_secret_json and not payment_config_encryption_available() and _is_production():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PAYMENT_CONFIG_ENCRYPTION_KEY is required to preserve sensitive payment configuration",
        )

    if bool(row.enabled) != enabled:
        changed_fields.append("enabled")
    row.enabled = enabled
    row.display_name = definition.display_name
    row.public_config_json = json.dumps(normalized_public, ensure_ascii=False, sort_keys=True)
    row.updated_by_id = admin_user_id
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return build_safe_provider_config(db, provider_key), sorted(set(changed_fields))


def validate_provider_config_payload(
    *,
    provider_key: str,
    public_config: dict[str, Any] | None,
    secret_values: dict[str, str] | None,
    existing_safe_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    definition = get_managed_provider_definition(provider_key)
    normalized_public = _normalize_public_config(definition, public_config)
    errors: list[str] = []
    for field in definition.required_public_fields:
        value = normalized_public.get(field)
        if value in {None, ""}:
            errors.append(f"{field} is required")
        elif field.endswith("_amount_cents") and int(value or 0) <= 0:
            errors.append(f"{field} must be greater than 0")

    existing_secret_status = (existing_safe_config or {}).get("secret_fields") or {}
    for field in definition.required_secret_fields:
        has_existing = bool((existing_secret_status.get(field) or {}).get("configured"))
        has_incoming = bool(str((secret_values or {}).get(field) or "").strip())
        if not has_existing and not has_incoming:
            errors.append(f"{field} is required")

    signature_preview = None
    secret_key = str((secret_values or {}).get("secret_key") or "").strip()
    if provider_key == "gmpay" and secret_key:
        from app.domains.payment.providers import build_gmpay_signature

        signature_preview = build_gmpay_signature(
            {
                "amount": "9.90",
                "currency": normalized_public["currency"],
                "name": "PDF-Flow Pro monthly",
                "network": normalized_public["network"],
                "notify_url": "https://example.com/api/v1/payment/webhooks/gmpay",
                "order_id": "pf_validation",
                "pid": normalized_public["pid"],
                "token": normalized_public["token"],
            },
            secret_key,
        )

    checks = list(definition.validation_checks or ("required_fields", "local_schema"))

    return {
        "valid": not errors,
        "errors": errors,
        "checks": checks,
        "signature_preview_tail": signature_preview[-8:] if signature_preview else None,
    }
