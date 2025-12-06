"""
SmartKYC - Badges API
Badge generation and verification endpoints
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Merchant, Badge as BadgeModel, TrustScore as TrustScoreModel, BadgeLevel
from app.schemas import BadgeGenerateResponse, BadgeResponse, BadgeShareInfo
from app.api.auth import get_current_merchant
from app.services.qr_generator import QRCodeGenerator
from app.services.badge_generator import BadgeGenerator


router = APIRouter()


@router.post("/generate", response_model=BadgeGenerateResponse, status_code=status.HTTP_201_CREATED)
def generate_badge(
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Generate a badge for the authenticated merchant.

    Steps:
    1. Check if merchant has a TrustScore calculated
    2. Generate unique verification code
    3. Generate QR code image
    4. Generate badge image
    5. Save badge record to database
    6. Return badge information with URLs

    Requirements:
    - Merchant must have at least one TrustScore calculated

    Returns:
        BadgeGenerateResponse with badge image and QR code URLs
    """
    # Check if merchant has a TrustScore
    latest_trustscore = db.query(TrustScoreModel)\
        .filter(TrustScoreModel.merchant_id == merchant.id)\
        .order_by(TrustScoreModel.created_at.desc())\
        .first()

    if not latest_trustscore:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No TrustScore found. Please calculate your TrustScore first."
        )

    # Check if merchant already has an active badge
    existing_badge = db.query(BadgeModel)\
        .filter(BadgeModel.merchant_id == merchant.id)\
        .filter(BadgeModel.is_active == True)\
        .order_by(BadgeModel.issued_at.desc())\
        .first()

    if existing_badge:
        # Check if existing badge is still valid
        if existing_badge.expires_at > datetime.utcnow():
            # Return existing badge
            return BadgeGenerateResponse(
                id=existing_badge.id,
                merchant_id=existing_badge.merchant_id,
                badge_level=existing_badge.badge_level.value,
                trustscore=latest_trustscore.trustscore,
                verification_code=existing_badge.verification_code,
                badge_image_url=f"/data/badges/{merchant.id}/{existing_badge.badge_image_path.split('/')[-1]}" if existing_badge.badge_image_path else "",
                qr_code_url=f"/data/qrcodes/{merchant.id}/{existing_badge.qr_code_image_path.split('/')[-1]}" if existing_badge.qr_code_image_path else "",
                verification_url=f"https://verify.smartkyc.cm/verify/{existing_badge.verification_code}",
                issued_at=existing_badge.issued_at.isoformat(),
                expires_at=existing_badge.expires_at.isoformat(),
                is_active=existing_badge.is_active
            )
        else:
            # Deactivate expired badge
            existing_badge.is_active = False
            db.commit()

    # Generate unique verification code
    verification_code = str(uuid.uuid4())

    # Initialize generators
    qr_generator = QRCodeGenerator()
    badge_generator = BadgeGenerator()

    # Generate QR code
    try:
        qr_code_path = qr_generator.generate_qr_code(
            verification_code=verification_code,
            merchant_id=merchant.id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate QR code: {str(e)}"
        )

    # Generate badge image
    try:
        badge_image_path = badge_generator.generate_badge(
            badge_level=latest_trustscore.badge.value,
            trustscore=latest_trustscore.trustscore,
            business_name=merchant.business_name or merchant.email,
            merchant_id=merchant.id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate badge image: {str(e)}"
        )

    # Create badge record in database
    badge = BadgeModel(
        id=str(uuid.uuid4()),
        merchant_id=merchant.id,
        badge_level=BadgeLevel[latest_trustscore.badge.value],
        badge_image_path=badge_image_path,
        qr_code_data=f"https://verify.smartkyc.cm/verify/{verification_code}",
        qr_code_image_path=qr_code_path,
        verification_code=verification_code,
        issued_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=180),  # 6 months validity
        is_active=True
    )

    db.add(badge)
    db.commit()
    db.refresh(badge)

    # Build response
    return BadgeGenerateResponse(
        id=badge.id,
        merchant_id=badge.merchant_id,
        badge_level=badge.badge_level.value,
        trustscore=latest_trustscore.trustscore,
        verification_code=badge.verification_code,
        badge_image_url=f"/data/badges/{merchant.id}/{badge_image_path.split('/')[-1]}",
        qr_code_url=f"/data/qrcodes/{merchant.id}/{qr_code_path.split('/')[-1]}",
        verification_url=f"https://verify.smartkyc.cm/verify/{badge.verification_code}",
        issued_at=badge.issued_at.isoformat(),
        expires_at=badge.expires_at.isoformat(),
        is_active=badge.is_active
    )


@router.get("/current", response_model=Optional[BadgeResponse])
def get_current_badge(
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Get the current active badge for the authenticated merchant.

    Returns:
        Current active badge or None if no badge exists
    """
    badge = db.query(BadgeModel)\
        .filter(BadgeModel.merchant_id == merchant.id)\
        .filter(BadgeModel.is_active == True)\
        .order_by(BadgeModel.issued_at.desc())\
        .first()

    if not badge:
        return None

    return BadgeResponse(
        id=badge.id,
        merchant_id=badge.merchant_id,
        badge_level=badge.badge_level.value,
        badge_image_path=badge.badge_image_path,
        qr_code_data=badge.qr_code_data,
        qr_code_image_path=badge.qr_code_image_path,
        verification_code=badge.verification_code,
        issued_at=badge.issued_at,
        expires_at=badge.expires_at,
        is_active=badge.is_active
    )


@router.get("/share", response_model=BadgeShareInfo)
def get_badge_share_info(
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Get sharing information for the merchant's badge.

    Returns:
        Badge sharing information including URLs and share message
    """
    badge = db.query(BadgeModel)\
        .filter(BadgeModel.merchant_id == merchant.id)\
        .filter(BadgeModel.is_active == True)\
        .order_by(BadgeModel.issued_at.desc())\
        .first()

    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active badge found. Please generate a badge first."
        )

    # Get latest TrustScore
    latest_trustscore = db.query(TrustScoreModel)\
        .filter(TrustScoreModel.merchant_id == merchant.id)\
        .order_by(TrustScoreModel.created_at.desc())\
        .first()

    trustscore_value = latest_trustscore.trustscore if latest_trustscore else 0

    # Get base URL from env (e.g., https://xyz.ngrok-free.app/auth/callback -> https://xyz.ngrok-free.app)
    import os
    callback_url = os.getenv("VITE_BACKEND_CALLBACK_URL", "http://localhost:8000/auth/callback")
    base_url = callback_url.replace("/auth/callback", "")
    
    verification_url = f"{base_url}/verify/{badge.verification_code}"

    share_message = (
        f"🏆 {merchant.business_name or 'Mon entreprise'} est certifié SmartKYC !\n\n"
        f"📊 TrustScore: {trustscore_value}/1000\n"
        f"🥇 Badge: {badge.badge_level.value}\n\n"
        f"Vérifiez notre badge de confiance:\n"
        f"{verification_url}\n\n"
        f"#SmartKYC #B2BAfrica #TrustScore"
    )

    return BadgeShareInfo(
        verification_code=badge.verification_code,
        verification_url=verification_url,
        qr_code_url=f"/data/qrcodes/{merchant.id}/{badge.qr_code_image_path.split('/')[-1]}" if badge.qr_code_image_path else "",
        badge_image_url=f"/data/badges/{merchant.id}/{badge.badge_image_path.split('/')[-1]}" if badge.badge_image_path else "",
        share_message=share_message
    )


@router.delete("/{badge_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_badge(
    badge_id: str,
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Revoke (deactivate) a badge.

    Args:
        badge_id: Badge UUID
        merchant: Authenticated merchant
        db: Database session

    Returns:
        204 No Content on success
    """
    badge = db.query(BadgeModel)\
        .filter(BadgeModel.id == badge_id)\
        .filter(BadgeModel.merchant_id == merchant.id)\
        .first()

    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Badge not found"
        )

    # Deactivate badge (don't delete, keep for history)
    badge.is_active = False
    db.commit()

    return None
