"""Public pricing catalog schemas."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.admin import PricingProviderMappings


class PublicPricingPlan(BaseModel):
    plan_key: Literal["free", "pro_monthly", "pro_yearly", "enterprise"]
    display_name: str
    is_public: bool
    price_amount_cents: int
    display_price: str
    currency: str
    billing_interval: str
    description: Optional[str] = None
    provider_mappings: PricingProviderMappings = Field(default_factory=PricingProviderMappings)
    sort_order: int
    highlighted: bool
    updated_at: datetime | None = None


class PublicPricingPlanList(BaseModel):
    source: str
    plans: list[PublicPricingPlan]
