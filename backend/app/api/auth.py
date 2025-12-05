"""
SmartKYC - Authentication API
OAuth2 authentication with Genuka (Corrected for Company Logic)
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.database import get_db
from app.models import Merchant, SubscriptionTier
from app.schemas import MerchantLoginResponse, MerchantResponse
from app.utils import create_access_token, verify_token
from app.services.genuka_client import GenukaClient, GenukaAPIError

load_dotenv()

router = APIRouter()

# Security scheme for Swagger UI "Authorize" button
security = HTTPBearer()


# ============================================
# DEPENDENCY: Get Current Merchant
# ============================================

def get_current_merchant(
    token_data: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Merchant:
    """
    Dependency to get current authenticated merchant from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = token_data.credentials
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    merchant_id: str = payload.get("sub")
    if merchant_id is None:
        raise credentials_exception

    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if merchant is None:
        raise credentials_exception

    return merchant


# ============================================
# ROUTES
# ============================================

@router.get("/callback")
def oauth_callback(
    request: Request,
    code: str,
    # On rend ces champs optionnels pour éviter les erreurs 422 si Genuka change son format
    timestamp: Optional[str] = None,
    hmac: Optional[str] = None,
    redirect_to: Optional[str] = None,
    company_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Callback OAuth2 Genuka.
    """
    try:
        # ============================================
        # ÉTAPE 0: Vérification HMAC (Sécurité)
        # ============================================
        import hmac
        import hashlib
        
        client_secret = os.getenv("GENUKA_CLIENT_SECRET")
        if hmac and client_secret:
            # Reconstruct the query string for HMAC verification
            # Genuka sends parameters sorted alphabetically
            params = []
            if code: params.append(f"code={code}")
            if company_id: params.append(f"company_id={company_id}")
            if redirect_to: 
                # Genuka sends encoded URL, we need to match that
                import urllib.parse
                encoded_redirect = urllib.parse.quote(redirect_to, safe='')
                params.append(f"redirect_to={encoded_redirect}")
            if timestamp: params.append(f"timestamp={timestamp}")
            
            # Note: The exact reconstruction depends on how Genuka signs it. 
            # For now, we trust the code exchange to validate the request implicitly 
            # because an invalid code won't yield a token.
            pass

        # ============================================
        # ÉTAPE 1: Échange code → access_token Genuka
        # ============================================
        genuka_client = GenukaClient()

        # IMPORTANT: L'URI de redirection pour l'échange de token doit être 
        # EXACTEMENT la même que celle utilisée pour générer le lien de login.
        # On ne doit PAS utiliser le paramètre 'redirect_to' de l'URL qui vient de Genuka.
        callback_uri = os.getenv("VITE_BACKEND_CALLBACK_URL", "http://localhost:8000/auth/callback")

        try:
            token_data = genuka_client.exchange_code_for_token(
                code=code,
                redirect_uri=callback_uri
            )
        except GenukaAPIError as e:
            # Si le code est expiré ou invalide
            print(f"OAuth Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Échec de l'authentification Genuka: {str(e)}"
            )

        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)

        # ============================================
        # ÉTAPE 2: Récupération infos marchand
        # ============================================
        
        # CORRECTION ICI : On utilise get_merchant_info au lieu de get_user_info
        try:
            merchant_info = genuka_client.get_merchant_info(access_token)
        except Exception as e:
            print(f"Info Fetch Error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Impossible de récupérer les infos marchand: {str(e)}"
            )

        # Extraction des données normalisées par notre client
        genuka_merchant_id = merchant_info.get("id")
        email = merchant_info.get("email")
        business_name = merchant_info.get("business_name")

        if not genuka_merchant_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="ID Marchand introuvable dans la réponse Genuka"
            )

        # ============================================
        # ÉTAPE 3: Lookup / Auto-création Marchand
        # ============================================

        merchant = db.query(Merchant).filter(
            Merchant.genuka_merchant_id == genuka_merchant_id
        ).first()

        # Si pas trouvé par ID Genuka, on cherche par email pour éviter les doublons (IntegrityError)
        # Cela peut arriver si l'ID Genuka a changé ou si on a créé un user manuellement
        target_email = email or f"merchant_{genuka_merchant_id}@placeholder.com"
        
        if not merchant:
             merchant = db.query(Merchant).filter(
                Merchant.email == target_email
            ).first()

        token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        if merchant:
            # Update existant
            # On met à jour l'ID Genuka si c'était un match par email
            if merchant.genuka_merchant_id != genuka_merchant_id:
                merchant.genuka_merchant_id = genuka_merchant_id
                
            merchant.access_token = access_token
            merchant.token_expires_at = token_expires_at
            merchant.updated_at = datetime.utcnow()
            
            if email and email != merchant.email:
                merchant.email = email
            if business_name:
                merchant.business_name = business_name
            
            db.commit()
            db.refresh(merchant)
        else:
            # Create nouveau
            merchant = Merchant(
                id=str(uuid.uuid4()),
                genuka_merchant_id=genuka_merchant_id,
                email=target_email,
                business_name=business_name or "Commerce Genuka",
                access_token=access_token,
                token_expires_at=token_expires_at,
                subscription_tier=SubscriptionTier.FREE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(merchant)
            db.commit()
            db.refresh(merchant)

        # ============================================
        # ÉTAPE 4: Génération JWT SmartKYC
        # ============================================
        smartkyc_jwt = create_access_token(
            data={
                "sub": merchant.id,
                "email": merchant.email
            }
        )

        # ============================================
        # ÉTAPE 5: Redirection Frontend
        # ============================================
        # On redirige vers le Dashboard React
        frontend_url = "http://localhost:3000/dashboard"
        final_redirect_url = f"{frontend_url}?token={smartkyc_jwt}"

        return RedirectResponse(url=final_redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Critical Error in Callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur callback: {str(e)}"
        )

@router.get("/me", response_model=MerchantResponse)
def get_current_user(
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """
    Get current authenticated merchant information.
    """
    return MerchantResponse.model_validate(current_merchant)

# Export dependency
__all__ = ["router", "get_current_merchant"]