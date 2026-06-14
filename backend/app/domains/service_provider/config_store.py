"""Admin-managed OCR/Office service provider configuration storage."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import ServiceProviderConfig as ServiceProviderConfigModel

SENSITIVE_FIELD_MARKERS = (
    "secret",
    "private",
    "token",
    "certificate",
    "cert",
    "key",
)


@dataclass(frozen=True)
class ServiceProviderFieldDefinition:
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
class ManagedServiceProviderDefinition:
    service_key: str
    provider_key: str
    display_name: str
    description: str
    public_defaults: dict[str, Any]
    public_fields: tuple[ServiceProviderFieldDefinition, ...]
    secret_fields: tuple[ServiceProviderFieldDefinition, ...] = ()
    validation_checks: tuple[str, ...] = ()
    setup_notes: tuple[str, ...] = ()
    runtime_fallback: str = ""

    @property
    def required_public_fields(self) -> tuple[str, ...]:
        return tuple(field.key for field in self.public_fields if field.required)

    @property
    def secret_field_keys(self) -> tuple[str, ...]:
        return tuple(field.key for field in self.secret_fields)

    @property
    def required_secret_fields(self) -> tuple[str, ...]:
        return tuple(field.key for field in self.secret_fields if field.required)


OCR_DEFAULT_PUBLIC_CONFIG: dict[str, Any] = {
    "tesseract_path": settings.TESSERACT_PATH or "",
    "default_language": (settings.OCR_LANGUAGES[0] if settings.OCR_LANGUAGES else "eng"),
    "languages": ",".join(settings.OCR_LANGUAGES),
}

OFFICE_DEFAULT_PUBLIC_CONFIG: dict[str, Any] = {
    "binary_path": "libreoffice",
    "timeout_seconds": 60,
}


MANAGED_SERVICE_PROVIDERS: dict[str, ManagedServiceProviderDefinition] = {
    "local_tesseract": ManagedServiceProviderDefinition(
        service_key="ocr",
        provider_key="local_tesseract",
        display_name="Local Tesseract",
        description="Local OCR execution using the server-installed Tesseract binary.",
        public_defaults=OCR_DEFAULT_PUBLIC_CONFIG,
        public_fields=(
            ServiceProviderFieldDefinition(
                key="tesseract_path",
                label="Tesseract Path",
                input_type="text",
                placeholder="Optional override",
                help_text="Leave empty to use the server default PATH lookup.",
            ),
            ServiceProviderFieldDefinition(
                key="default_language",
                label="Default Language",
                required=True,
                placeholder="eng",
                help_text="Used when the request does not specify a language.",
            ),
            ServiceProviderFieldDefinition(
                key="languages",
                label="Languages",
                required=True,
                placeholder="eng,chi_sim,spa",
                help_text="Comma-separated language packs available on the server.",
            ),
        ),
        validation_checks=("required_fields", "tesseract_binary_check", "language_pack_check"),
        setup_notes=(
            "Keep the server Tesseract binary installed.",
            "Language packs are controlled by the runtime server image, not by the admin UI.",
        ),
        runtime_fallback="settings.TESSERACT_PATH + settings.OCR_LANGUAGES",
    ),
    "local_libreoffice": ManagedServiceProviderDefinition(
        service_key="office",
        provider_key="local_libreoffice",
        display_name="Local LibreOffice",
        description="Local Office-to-PDF conversion using the server-installed LibreOffice binary.",
        public_defaults=OFFICE_DEFAULT_PUBLIC_CONFIG,
        public_fields=(
            ServiceProviderFieldDefinition(
                key="binary_path",
                label="Binary Path",
                required=True,
                placeholder="libreoffice",
                help_text="Command used to launch LibreOffice headless conversion.",
            ),
            ServiceProviderFieldDefinition(
                key="timeout_seconds",
                label="Timeout Seconds",
                input_type="number",
                required=True,
                min_value=10,
                help_text="Maximum conversion time before the job is retried or failed.",
            ),
        ),
        validation_checks=("required_fields", "libreoffice_binary_check"),
        setup_notes=(
            "Keep LibreOffice installed in the backend container image.",
            "This module only controls runtime settings, not the conversion workflow.",
        ),
        runtime_fallback="libreoffice command + hard-coded task timeout",
    ),
}


def is_managed_service_provider(provider_key: str) -> bool:
    return provider_key in MANAGED_SERVICE_PROVIDERS


def list_managed_service_provider_keys() -> list[str]:
    return list(MANAGED_SERVICE_PROVIDERS)


def get_managed_service_provider_definition(provider_key: str) -> ManagedServiceProviderDefinition:
    try:
        return MANAGED_SERVICE_PROVIDERS[provider_key]
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Managed service provider not found",
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
        detail="PAYMENT_CONFIG_ENCRYPTION_KEY is required for sensitive service configuration",
    )


def service_config_encryption_available() -> bool:
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
    if not service_config_encryption_available():
        if _is_production():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="PAYMENT_CONFIG_ENCRYPTION_KEY is required to read sensitive service configuration",
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
            detail="Service provider secrets could not be decrypted",
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


def _field_to_metadata(field: ServiceProviderFieldDefinition) -> dict[str, Any]:
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


def _provider_metadata(definition: ManagedServiceProviderDefinition) -> dict[str, Any]:
    return {
        "service_key": definition.service_key,
        "provider_key": definition.provider_key,
        "display_name": definition.display_name,
        "description": definition.description,
        "validation_checks": list(definition.validation_checks),
        "setup_notes": list(definition.setup_notes),
        "runtime_fallback": definition.runtime_fallback,
        "fields": {
            "public": [_field_to_metadata(field) for field in definition.public_fields],
            "secret": [_field_to_metadata(field) for field in definition.secret_fields],
        },
    }


def _secret_status(definition: ManagedServiceProviderDefinition, row: ServiceProviderConfigModel | None) -> dict[str, dict[str, str | bool]]:
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


def _merged_public_config(definition: ManagedServiceProviderDefinition, row: ServiceProviderConfigModel | None) -> dict[str, Any]:
    config = dict(definition.public_defaults)
    config.update(_load_json_object(row.public_config_json if row else None))
    return config


def _normalize_public_config(definition: ManagedServiceProviderDefinition, public_config: dict[str, Any] | None) -> dict[str, Any]:
    data = dict(definition.public_defaults)
    for key, value in (public_config or {}).items():
        if key not in definition.public_defaults:
            continue
        if key.endswith("_seconds"):
            data[key] = int(value or 0)
        else:
            data[key] = str(value or "").strip()
    return data


def _is_public_config_complete(definition: ManagedServiceProviderDefinition, public_config: dict[str, Any]) -> bool:
    field_map = {field.key: field for field in definition.public_fields}
    for field_key in definition.required_public_fields:
        value = public_config.get(field_key)
        if value is None or value == "":
            return False
        if field_key.endswith("_seconds") and int(value) <= 0:
            return False
        min_value = field_map[field_key].min_value
        if min_value is not None and int(value) < min_value:
            return False
    return True


def _command_exists(command: str) -> bool:
    command = str(command or "").strip()
    if not command:
        return False
    if os.path.isabs(command) or os.sep in command:
        return os.path.exists(command)
    return shutil.which(command) is not None


def _readiness_errors(definition: ManagedServiceProviderDefinition, public_config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    field_map = {field.key: field for field in definition.public_fields}
    for field_key in definition.required_public_fields:
        value = public_config.get(field_key)
        if value in {None, ""}:
            errors.append(f"{field_key} is required")
            continue
        if field_key.endswith("_seconds") and int(value or 0) <= 0:
            errors.append(f"{field_key} must be greater than 0")
        min_value = field_map[field_key].min_value
        if min_value is not None and int(value or 0) < min_value:
            errors.append(f"{field_key} must be at least {min_value}")

    if definition.provider_key == "local_tesseract":
        binary = str(public_config.get("tesseract_path") or settings.TESSERACT_PATH or "tesseract").strip()
        if not _command_exists(binary):
            errors.append("tesseract binary is not available")
        languages = [
            item.strip()
            for item in str(public_config.get("languages") or "").split(",")
            if item.strip()
        ]
        default_language = str(public_config.get("default_language") or "").strip()
        if default_language and languages and default_language not in languages:
            errors.append("default_language must be included in languages")
    elif definition.provider_key == "local_libreoffice":
        binary = str(public_config.get("binary_path") or "libreoffice").strip()
        if not _command_exists(binary):
            errors.append("libreoffice binary is not available")

    return errors


def get_service_provider_config_row(
    db: Session,
    service_key: str,
    provider_key: str,
) -> ServiceProviderConfigModel | None:
    return db.query(ServiceProviderConfigModel).filter(
        ServiceProviderConfigModel.service_key == service_key,
        ServiceProviderConfigModel.provider_key == provider_key,
    ).first()


def get_service_provider_runtime_config(db: Session, service_key: str, provider_key: str) -> dict[str, Any] | None:
    definition = MANAGED_SERVICE_PROVIDERS.get(provider_key)
    if not definition or definition.service_key != service_key:
        return None
    row = get_service_provider_config_row(db, service_key, provider_key)
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
        "service_key": service_key,
        "provider_key": provider_key,
        "display_name": row.display_name or definition.display_name,
        "enabled": row.enabled,
        "priority": row.priority,
        "public_config": public_config,
        "secrets": secrets,
    }


def build_safe_service_provider_config(
    db: Session,
    service_key: str,
    provider_key: str,
) -> dict[str, Any]:
    definition = get_managed_service_provider_definition(provider_key)
    if definition.service_key != service_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Managed service provider not found",
        )
    row = get_service_provider_config_row(db, service_key, provider_key)
    public_config = _merged_public_config(definition, row)
    secret_status = _secret_status(definition, row)
    config_errors = _readiness_errors(definition, public_config)
    missing_public = [field for field in definition.required_public_fields if public_config.get(field) in {None, ""}]
    missing_secret = [field for field in definition.required_secret_fields if not secret_status[field]["configured"]]
    if row and not row.enabled:
        readiness_status = "disabled"
    elif not missing_public and not missing_secret and not config_errors:
        readiness_status = "ready"
    else:
        readiness_status = "missing_config"
    readiness_label = {
        "ready": "Ready",
        "disabled": "Disabled",
        "missing_config": "Needs config",
    }[readiness_status]
    readiness_detail = {
        "ready": "Required fields and lightweight local checks are passing.",
        "disabled": "Provider is saved but disabled; runtime will use fallback.",
        "missing_config": "Required fields or lightweight local checks need attention.",
    }[readiness_status]
    return {
        "service_key": definition.service_key,
        "provider_key": definition.provider_key,
        "display_name": row.display_name if row else definition.display_name,
        "enabled": bool(row.enabled) if row else False,
        "priority": row.priority if row else 100,
        "configured": not missing_public and not missing_secret,
        "public_config": public_config,
        "secret_fields": secret_status,
        "required_public_fields": list(definition.required_public_fields),
        "required_secret_fields": list(definition.required_secret_fields),
        "missing_config_keys": missing_public + missing_secret,
        "updated_at": row.updated_at if row else None,
        "encryption_available": service_config_encryption_available(),
        "metadata": _provider_metadata(definition),
        "readiness": {
            "status": readiness_status,
            "label": readiness_label,
            "detail": readiness_detail,
            "missing_config_keys": missing_public + missing_secret,
            "validation_checks": list(definition.validation_checks),
        },
    }


def list_safe_service_provider_configs(db: Session, service_key: str) -> list[dict[str, Any]]:
    return [
        build_safe_service_provider_config(db, service_key, provider_key)
        for provider_key, definition in MANAGED_SERVICE_PROVIDERS.items()
        if definition.service_key == service_key
    ]


def update_service_provider_config(
    db: Session,
    *,
    service_key: str,
    provider_key: str,
    enabled: bool,
    priority: int,
    public_config: dict[str, Any] | None,
    secret_values: dict[str, str] | None,
    admin_user_id: int,
) -> tuple[dict[str, Any], list[str]]:
    definition = get_managed_service_provider_definition(provider_key)
    if definition.service_key != service_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Managed service provider not found",
        )
    row = get_service_provider_config_row(db, service_key, provider_key)
    if row is None:
        row = ServiceProviderConfigModel(
            service_key=definition.service_key,
            provider_key=definition.provider_key,
            display_name=definition.display_name,
            enabled=False,
            priority=priority,
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
    if incoming_secrets and not service_config_encryption_available() and _is_production():
        _require_encryption_key()
    for field, value in incoming_secrets.items():
        if merged_secrets.get(field) != value:
            changed_fields.append(field)
        merged_secrets[field] = value

    if incoming_secrets:
        row.encrypted_secret_json = _encrypt_secret_payload(merged_secrets)
        row.secret_fingerprint_json = json.dumps(_fingerprints(merged_secrets), sort_keys=True)
    elif row.encrypted_secret_json and not service_config_encryption_available() and _is_production():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PAYMENT_CONFIG_ENCRYPTION_KEY is required to preserve sensitive service configuration",
        )

    if bool(row.enabled) != enabled:
        changed_fields.append("enabled")
    if int(row.priority) != int(priority):
        changed_fields.append("priority")
    row.enabled = enabled
    row.priority = int(priority)
    row.display_name = definition.display_name
    row.public_config_json = json.dumps(normalized_public, ensure_ascii=False, sort_keys=True)
    row.updated_by_id = admin_user_id
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return build_safe_service_provider_config(db, service_key, provider_key), sorted(set(changed_fields))


def validate_service_provider_config_payload(
    *,
    service_key: str,
    provider_key: str,
    public_config: dict[str, Any] | None,
    secret_values: dict[str, str] | None,
    existing_safe_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    definition = get_managed_service_provider_definition(provider_key)
    if definition.service_key != service_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Managed service provider not found",
        )
    normalized_public = _normalize_public_config(definition, public_config)
    errors: list[str] = []
    errors.extend(_readiness_errors(definition, normalized_public))

    existing_secret_status = (existing_safe_config or {}).get("secret_fields") or {}
    for field in definition.required_secret_fields:
        has_existing = bool((existing_secret_status.get(field) or {}).get("configured"))
        has_incoming = bool(str((secret_values or {}).get(field) or "").strip())
        if not has_existing and not has_incoming:
            errors.append(f"{field} is required")

    checks = list(definition.validation_checks or ("required_fields", "local_schema"))
    if provider_key == "local_tesseract":
        checks = ["required_fields", "tesseract_binary_check", "language_pack_check"]
    elif provider_key == "local_libreoffice":
        checks = ["required_fields", "libreoffice_binary_check"]

    return {
        "valid": not errors,
        "errors": errors,
        "checks": checks,
        "signature_preview_tail": None,
    }
