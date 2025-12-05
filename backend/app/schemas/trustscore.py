"""
SmartKYC - TrustScore Schemas
Pydantic schemas for TrustScore data validation
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class TrustScoreMetrics(BaseModel):
    """Schema for TrustScore metrics breakdown"""
    documents: Dict[str, Any]
    historique: Dict[str, Any]
    comportement: Dict[str, Any]
    financiers: Dict[str, Any]


class TrustScoreBase(BaseModel):
    """Base TrustScore schema"""
    trustscore: int = Field(..., ge=0, le=1000, description="TrustScore value (0-1000)")
    badge: str = Field(..., description="Badge level (NONE, BRONZE, SILVER, GOLD, PLATINUM)")
    calculation_mode: str = Field(..., description="Calculation mode (COLD_START or NORMAL)")


class TrustScoreResponse(TrustScoreBase):
    """
    Schema for TrustScore response.

    Returned when fetching or calculating a TrustScore.
    """
    id: str
    merchant_id: str
    metrics: Dict[str, Any]
    valid_until: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class TrustScoreCalculateResponse(BaseModel):
    """
    Schema for TrustScore calculation response.

    Extended response with additional info after calculation.
    """
    trustscore: int = Field(..., ge=0, le=1000)
    badge: str
    calculation_mode: str
    metrics: Dict[str, Any]
    valid_until: str
    created_at: str
    saved_to_db: bool = True
    trustscore_id: Optional[str] = None


class TrustScoreHistoryItem(BaseModel):
    """Schema for a single TrustScore history item"""
    id: str
    trustscore: int
    badge: str
    calculation_mode: str
    created_at: datetime

    class Config:
        from_attributes = True


class TrustScoreHistoryResponse(BaseModel):
    """Schema for TrustScore history response"""
    merchant_id: str
    total_count: int
    scores: list[TrustScoreHistoryItem]
