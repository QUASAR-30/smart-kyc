"""
SmartKYC - TrustScore API
API endpoints for TrustScore calculation and retrieval
"""

import uuid
import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Merchant, TrustScore as TrustScoreModel, CalculationMode
# Import BadgeLevel directly from trustscore model to avoid conflict with badge model
from app.models.trustscore import BadgeLevel as TrustScoreBadgeLevel
from app.schemas import (
    TrustScoreResponse,
    TrustScoreCalculateResponse,
    TrustScoreHistoryResponse,
    TrustScoreHistoryItem
)
from app.api.auth import get_current_merchant
from app.services.trustscore_calculator import TrustScoreCalculator


router = APIRouter()


@router.post("/calculate", response_model=TrustScoreCalculateResponse)
def calculate_trustscore(
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Calculate TrustScore for the authenticated merchant.

    This endpoint:
    1. Retrieves merchant data from Genuka (mock)
    2. Calculates TrustScore using TrustScoreCalculator
    3. Saves the result to the database
    4. Returns the complete TrustScore with metrics

    Args:
        merchant: Authenticated merchant (from JWT token)
        db: Database session

    Returns:
        TrustScore calculation result with metrics

    Example:
        POST /api/trustscores/calculate
        Authorization: Bearer <token>

        Response:
        {
            "trustscore": 828,
            "badge": "GOLD",
            "calculation_mode": "NORMAL",
            "metrics": {...},
            "valid_until": "2026-06-05T00:00:00",
            "created_at": "2025-12-05T00:00:00",
            "saved_to_db": true,
            "trustscore_id": "..."
        }
    """
    try:
        # Initialize TrustScore calculator
        calculator = TrustScoreCalculator(merchant_id=merchant.id, db_session=db)

        # Calculate TrustScore
        result = calculator.calculate_trustscore(access_token=merchant.access_token)

        # Save to database
        trustscore_record = TrustScoreModel(
            id=str(uuid.uuid4()),
            merchant_id=merchant.id,
            trustscore=result['trustscore'],
            badge=TrustScoreBadgeLevel[result['badge']].value, # Use .value for SQLite
            metrics=json.dumps(result['metrics']),
            calculation_mode=CalculationMode[result['calculation_mode']].value, # Use .value for SQLite
            valid_until=datetime.fromisoformat(result['valid_until']),
            created_at=datetime.fromisoformat(result['created_at'])
        )

        db.add(trustscore_record)
        db.commit()
        db.refresh(trustscore_record)

        # Return response
        return TrustScoreCalculateResponse(
            trustscore=result['trustscore'],
            badge=result['badge'],
            calculation_mode=result['calculation_mode'],
            metrics=result['metrics'],
            valid_until=result['valid_until'],
            created_at=result['created_at'],
            saved_to_db=True,
            trustscore_id=trustscore_record.id
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating TrustScore: {str(e)}"
        )


@router.get("/latest", response_model=TrustScoreResponse)
def get_latest_trustscore(
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Get the latest TrustScore for the authenticated merchant.

    Args:
        merchant: Authenticated merchant (from JWT token)
        db: Database session

    Returns:
        Latest TrustScore with full details

    Raises:
        404: If no TrustScore exists for this merchant

    Example:
        GET /api/trustscores/latest
        Authorization: Bearer <token>

        Response:
        {
            "id": "...",
            "merchant_id": "...",
            "trustscore": 828,
            "badge": "GOLD",
            "calculation_mode": "NORMAL",
            "metrics": {...},
            "valid_until": "2026-06-05T00:00:00",
            "created_at": "2025-12-05T00:00:00"
        }
    """
    # Query latest TrustScore for this merchant
    latest_score = db.query(TrustScoreModel)\
        .filter(TrustScoreModel.merchant_id == merchant.id)\
        .order_by(TrustScoreModel.created_at.desc())\
        .first()

    if not latest_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No TrustScore found for this merchant. Please calculate one first."
        )

    # Parse metrics JSON
    metrics_dict = json.loads(latest_score.metrics) if isinstance(latest_score.metrics, str) else latest_score.metrics

    return TrustScoreResponse(
        id=latest_score.id,
        merchant_id=latest_score.merchant_id,
        trustscore=latest_score.trustscore,
        badge=latest_score.badge.value,
        calculation_mode=latest_score.calculation_mode.value,
        metrics=metrics_dict,
        valid_until=latest_score.valid_until,
        created_at=latest_score.created_at
    )


@router.get("/history", response_model=TrustScoreHistoryResponse)
def get_trustscore_history(
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
    limit: int = 5
):
    """
    Get TrustScore history for the authenticated merchant.

    Retrieves the last N TrustScore calculations for trend analysis.

    Args:
        merchant: Authenticated merchant (from JWT token)
        db: Database session
        limit: Number of scores to return (default: 5, max: 20)

    Returns:
        List of historical TrustScores

    Example:
        GET /api/trustscores/history?limit=5
        Authorization: Bearer <token>

        Response:
        {
            "merchant_id": "...",
            "total_count": 12,
            "scores": [
                {
                    "id": "...",
                    "trustscore": 850,
                    "badge": "GOLD",
                    "calculation_mode": "NORMAL",
                    "created_at": "2025-12-05T00:00:00"
                },
                ...
            ]
        }
    """
    # Limit parameter validation
    if limit < 1:
        limit = 5
    if limit > 20:
        limit = 20

    # Query TrustScore history
    scores = db.query(TrustScoreModel)\
        .filter(TrustScoreModel.merchant_id == merchant.id)\
        .order_by(TrustScoreModel.created_at.desc())\
        .limit(limit)\
        .all()

    # Get total count
    total_count = db.query(TrustScoreModel)\
        .filter(TrustScoreModel.merchant_id == merchant.id)\
        .count()

    # Convert to response format
    history_items = [
        TrustScoreHistoryItem(
            id=score.id,
            trustscore=score.trustscore,
            badge=score.badge.value,
            calculation_mode=score.calculation_mode.value,
            created_at=score.created_at
        )
        for score in scores
    ]

    return TrustScoreHistoryResponse(
        merchant_id=merchant.id,
        total_count=total_count,
        scores=history_items
    )


# Export router
__all__ = ["router"]
