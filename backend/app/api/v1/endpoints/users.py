"""
User management endpoints
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.account import delete_account, get_usage_stats, update_account
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UsageStats
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get("/me/stats", response_model=UsageStats)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's usage statistics
    """
    return get_usage_stats(db, current_user)


@router.patch("/me", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user information
    """
    return update_account(db, current_user, user_update)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user account
    I (Information Disclosure): GDPR compliance - user can delete their data
    """
    delete_account(db, current_user)
    return None
