"""
SmartKYC - Merchant Schemas
Pydantic schemas for merchant data validation
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class MerchantBase(BaseModel):
    """Base merchant schema with common fields"""
    email: EmailStr
    business_name: Optional[str] = None


class MerchantCreate(BaseModel):
    """
    Schema for creating a new merchant (auto-signup).

    For hackathon: Only email is required, merchant is auto-created.
    """
    email: EmailStr


class MerchantUpdate(BaseModel):
    """Schema for updating merchant information"""
    business_name: Optional[str] = None
    genuka_merchant_id: Optional[str] = None


class MerchantResponse(BaseModel):
    """
    Schema for merchant response data.

    Returned after authentication or when fetching merchant info.
    """
    id: str
    email: str
    business_name: Optional[str] = None
    genuka_merchant_id: Optional[str] = None
    subscription_tier: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows creating from ORM models


class MerchantLoginRequest(BaseModel):
    """
    Schema for mock login request.

    For hackathon: Simple email-based authentication.
    """
    # email: EmailStr
    code: str
    timestamp: float
    hmac: str
    redirect_to: str
    


class MerchantLoginResponse(BaseModel):
    """
    Schema for login response.

    Returns both the access token and merchant information.
    """
    access_token: str
    token_type: str = "bearer"
    merchant: MerchantResponse
