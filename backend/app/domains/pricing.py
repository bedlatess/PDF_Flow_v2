"""Admin-managed plan catalog with conservative fallback defaults."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domains.admin.audit import write_admin_audit
from app.models.user import PricingPlan, User
from app.schemas.admin import PricingPlanUpdate


ALLOWED_PLAN_KEYS = ("free", "pro_monthly", "pro_yearly", "enterprise")


@dataclass(frozen=True)
class DefaultPricingPlan:
    plan_key: str
    display_name: str
    is_public: bool
    price_amount_cents: int
    display_price: str
    currency: str
    billing_interval: str
    description: str
    provider_mappings: dict[str, Any]
    sort_order: int
    highlighted: bool = False


DEFAULT_PRICING_PLANS = [
    DefaultPricingPlan(
        plan_key="free",
        display_name="Free",
        is_public=True,
        price_amount_cents=0,
        display_price="$0",
        currency="USD",
        billing_interval="none",
        description="Core browser-first PDF tools for everyday work.",
        provider_mappings={},
        sort_order=10,
    ),
    DefaultPricingPlan(
        plan_key="pro_monthly",
        display_name="Pro Monthly",
        is_public=True,
        price_amount_cents=990,
        display_price="$9.90",
        currency="USD",
        billing_interval="month",
        description="Monthly Pro access for cloud and advanced document workflows.",
        provider_mappings={
            "stripe": {"price_id": settings.STRIPE_PRICE_ID_MONTHLY or ""},
            "paypal": {"plan_id": "", "product_id": ""},
            "gmpay": {"amount_cents": 990, "currency": "CNY", "token": "usdt", "network": "tron"},
        },
        sort_order=20,
        highlighted=True,
    ),
    DefaultPricingPlan(
        plan_key="pro_yearly",
        display_name="Pro Yearly",
        is_public=True,
        price_amount_cents=7900,
        display_price="$79",
        currency="USD",
        billing_interval="year",
        description="Annual Pro access with the same entitlement period used by the current checkout.",
        provider_mappings={
            "stripe": {"price_id": settings.STRIPE_PRICE_ID_YEARLY or ""},
            "paypal": {"plan_id": "", "product_id": ""},
            "gmpay": {"amount_cents": 7900, "currency": "CNY", "token": "usdt", "network": "tron"},
        },
        sort_order=30,
    ),
    DefaultPricingPlan(
        plan_key="enterprise",
        display_name="Enterprise",
        is_public=True,
        price_amount_cents=0,
        display_price="Custom",
        currency="USD",
        billing_interval="custom",
        description="Custom workflows, higher limits, and operational support.",
        provider_mappings={},
        sort_order=40,
    ),
]

DEFAULT_PLAN_BY_KEY = {plan.plan_key: plan for plan in DEFAULT_PRICING_PLANS}
CHECKOUT_PLAN_ALIASES = {
    "monthly": "pro_monthly",
    "yearly": "pro_yearly",
}
CHECKOUT_PERIOD_DAYS = {
    "pro_monthly": 30,
    "pro_yearly": 365,
    "monthly": 30,
    "yearly": 365,
}


def normalize_plan_key(plan_key: str) -> str:
    return CHECKOUT_PLAN_ALIASES.get(plan_key, plan_key)


def _safe_json_loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _normalize_provider_mappings(value: dict[str, Any] | None) -> dict[str, Any]:
    value = value or {}
    stripe = value.get("stripe") if isinstance(value.get("stripe"), dict) else {}
    paypal = value.get("paypal") if isinstance(value.get("paypal"), dict) else {}
    gmpay = value.get("gmpay") if isinstance(value.get("gmpay"), dict) else {}
    return {
        "stripe": {"price_id": str(stripe.get("price_id") or "")},
        "paypal": {
            "plan_id": str(paypal.get("plan_id") or ""),
            "product_id": str(paypal.get("product_id") or ""),
        },
        "gmpay": {
            "amount_cents": int(gmpay.get("amount_cents") or 0),
            "currency": str(gmpay.get("currency") or "CNY").upper(),
            "token": str(gmpay.get("token") or "usdt").lower(),
            "network": str(gmpay.get("network") or "tron").lower(),
        },
    }


def _plan_to_dict(plan: PricingPlan) -> dict[str, Any]:
    return {
        "id": plan.id,
        "plan_key": plan.plan_key,
        "display_name": plan.display_name,
        "is_public": plan.is_public,
        "price_amount_cents": plan.price_amount_cents,
        "display_price": plan.display_price,
        "currency": plan.currency,
        "billing_interval": plan.billing_interval,
        "description": plan.description,
        "provider_mappings": _normalize_provider_mappings(
            _safe_json_loads(plan.provider_mappings_json)
        ),
        "sort_order": plan.sort_order,
        "highlighted": plan.highlighted,
        "updated_at": plan.updated_at,
    }


def seed_pricing_plans(db: Session) -> None:
    existing = {item[0] for item in db.query(PricingPlan.plan_key).all()}
    for default in DEFAULT_PRICING_PLANS:
        if default.plan_key in existing:
            continue
        db.add(
            PricingPlan(
                plan_key=default.plan_key,
                display_name=default.display_name,
                is_public=default.is_public,
                price_amount_cents=default.price_amount_cents,
                display_price=default.display_price,
                currency=default.currency,
                billing_interval=default.billing_interval,
                description=default.description,
                provider_mappings_json=json.dumps(
                    _normalize_provider_mappings(default.provider_mappings),
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                sort_order=default.sort_order,
                highlighted=default.highlighted,
            )
        )
    db.commit()


def list_pricing_plans(db: Session) -> list[dict[str, Any]]:
    seed_pricing_plans(db)
    return [
        _plan_to_dict(plan)
        for plan in db.query(PricingPlan).order_by(PricingPlan.sort_order, PricingPlan.plan_key).all()
    ]


def list_public_pricing_plans(db: Session) -> dict[str, Any]:
    plans = (
        db.query(PricingPlan)
        .filter(PricingPlan.is_public == True)  # noqa: E712
        .order_by(PricingPlan.sort_order, PricingPlan.plan_key)
        .all()
    )
    return {
        "source": "db" if plans else "fallback",
        "plans": [_plan_to_dict(plan) for plan in plans],
    }


def update_pricing_plan(
    db: Session,
    *,
    plan_key: str,
    payload: PricingPlanUpdate,
    request: Request,
    admin: User,
) -> dict[str, Any]:
    seed_pricing_plans(db)
    normalized_key = normalize_plan_key(plan_key)
    if normalized_key not in ALLOWED_PLAN_KEYS or payload.plan_key != normalized_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pricing plan key")

    plan = db.query(PricingPlan).filter(PricingPlan.plan_key == normalized_key).first()
    if not plan:
        plan = PricingPlan(plan_key=normalized_key)
        db.add(plan)

    previous = _plan_to_dict(plan) if plan.id else {}
    data = payload.model_dump(mode="json")
    mappings = _normalize_provider_mappings(data.pop("provider_mappings"))
    for field, value in data.items():
        setattr(plan, field, value)
    plan.provider_mappings_json = json.dumps(mappings, ensure_ascii=False, sort_keys=True)
    plan.updated_by_id = admin.id
    current = {
        **data,
        "provider_mappings": mappings,
    }

    changed_fields = [
        field
        for field in [
            "display_name",
            "is_public",
            "price_amount_cents",
            "display_price",
            "currency",
            "billing_interval",
            "description",
            "provider_mappings",
            "sort_order",
            "highlighted",
        ]
        if previous.get(field) != current.get(field)
    ]
    detail = f"changed_fields={','.join(changed_fields) or 'none'}"
    write_admin_audit(db, request, admin, "update", "pricing_plan", normalized_key, detail)
    db.commit()
    db.refresh(plan)
    return _plan_to_dict(plan)


def get_checkout_plan(db: Session, plan_key: str) -> dict[str, Any] | None:
    normalized_key = normalize_plan_key(plan_key)
    plan = db.query(PricingPlan).filter(PricingPlan.plan_key == normalized_key).first()
    if plan:
        data = _plan_to_dict(plan)
        data["checkout_plan_key"] = normalized_key
        data["period_days"] = CHECKOUT_PERIOD_DAYS.get(normalized_key)
        return data

    default = DEFAULT_PLAN_BY_KEY.get(normalized_key)
    if not default:
        return None
    return {
        "checkout_plan_key": normalized_key,
        "plan_key": default.plan_key,
        "display_name": default.display_name,
        "is_public": default.is_public,
        "price_amount_cents": default.price_amount_cents,
        "display_price": default.display_price,
        "currency": default.currency,
        "billing_interval": default.billing_interval,
        "description": default.description,
        "provider_mappings": _normalize_provider_mappings(default.provider_mappings),
        "sort_order": default.sort_order,
        "highlighted": default.highlighted,
        "period_days": CHECKOUT_PERIOD_DAYS.get(normalized_key),
    }
