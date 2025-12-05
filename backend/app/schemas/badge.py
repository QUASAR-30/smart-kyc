"""
SmartKYC - Badge Schemas
Pydantic schemas for badge generation and verification
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class BadgeGenerateResponse(BaseModel):
    """Response for badge generation."""
    id: str
    merchant_id: str
    badge_level: str
    trustscore: int
    verification_code: str
    badge_image_url: str
    qr_code_url: str
    verification_url: str
    issued_at: str
    expires_at: str
    is_active: bool = True

    class Config:
        from_attributes = True


class BadgeResponse(BaseModel):
    """Response for single badge."""
    id: str
    merchant_id: str
    badge_level: str
    badge_image_path: Optional[str] = None
    qr_code_data: Optional[str] = None
    qr_code_image_path: Optional[str] = None
    verification_code: str
    issued_at: datetime
    expires_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class BadgeVerificationResponse(BaseModel):
    """Response for public badge verification."""
    merchant_name: str
    business_name: str
    badge_level: str
    trustscore: int
    trustscore_badge: str  # Badge from TrustScore (may differ from badge_level)
    verification_status: str  # VALID, EXPIRED, REVOKED
    issued_at: str
    expires_at: str
    documents_verified: list[str]  # List of verified document types
    credit_recommendation: Optional[str] = None
    merchant_email: Optional[str] = None

    class Config:
        from_attributes = True


class BadgeShareInfo(BaseModel):
    """Information for sharing a badge."""
    verification_code: str
    verification_url: str
    qr_code_url: str
    badge_image_url: str
    share_message: str
