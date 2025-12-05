"""
SmartKYC - Token Schemas
Pydantic schemas for authentication tokens
"""

from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """
    JWT Token response schema.

    Used when returning authentication tokens to clients.
    """
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    JWT Token payload data schema.

    Represents the data encoded within a JWT token.
    """
    merchant_id: Optional[str] = None
    email: Optional[str] = None
