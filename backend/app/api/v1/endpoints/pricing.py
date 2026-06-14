"""Public pricing catalog endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.pricing import list_public_pricing_plans
from app.schemas.pricing import PublicPricingPlanList

router = APIRouter()


@router.get("/plans", response_model=PublicPricingPlanList)
async def list_pricing_plans(db: Session = Depends(get_db)):
    """Return public DB-backed plans for the Pricing page."""
    return list_public_pricing_plans(db)
