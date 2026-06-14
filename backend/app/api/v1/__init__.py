"""
API v1 router
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, health, files, websocket, oauth, payment, enterprise, ai, advanced, admin, feedback, pricing

api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(oauth.router, prefix="/auth", tags=["oauth"])
api_router.include_router(payment.router, prefix="/payment", tags=["payment"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["pricing"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(files.router, tags=["files"])
api_router.include_router(websocket.router, tags=["websocket"])
api_router.include_router(enterprise.router, tags=["enterprise"])
api_router.include_router(ai.router, tags=["ai"])
api_router.include_router(advanced.router, tags=["advanced-pdf"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(feedback.router, tags=["feedback"])
