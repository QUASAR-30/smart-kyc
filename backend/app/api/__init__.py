"""
SmartKYC - API Endpoints
FastAPI routers for all API endpoints
"""

from app.api.auth import router as auth_router, get_current_merchant
from app.api.trustscores import router as trustscores_router
from app.api.documents import router as documents_router
from app.api.badges import router as badges_router
from app.api.verify import router as verify_router

__all__ = [
    "auth_router",
    "trustscores_router",
    "documents_router",
    "badges_router",
    "verify_router",
    "get_current_merchant",
]
