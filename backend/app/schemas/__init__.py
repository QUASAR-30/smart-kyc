"""
SmartKYC - Pydantic Schemas
Request/Response validation schemas
"""

from app.schemas.merchant import (
    MerchantBase,
    MerchantCreate,
    MerchantUpdate,
    MerchantResponse,
    MerchantLoginRequest,
    MerchantLoginResponse
)

from app.schemas.token import Token, TokenData

from app.schemas.trustscore import (
    TrustScoreMetrics,
    TrustScoreBase,
    TrustScoreResponse,
    TrustScoreCalculateResponse,
    TrustScoreHistoryItem,
    TrustScoreHistoryResponse
)

from app.schemas.document import (
    DocumentType,
    VerificationStatus,
    DocumentUploadResponse,
    DocumentVerificationResult,
    DocumentResponse,
    DocumentListResponse
)

from app.schemas.badge import (
    BadgeGenerateResponse,
    BadgeResponse,
    BadgeVerificationResponse,
    BadgeShareInfo
)

__all__ = [
    # Merchant schemas
    "MerchantBase",
    "MerchantCreate",
    "MerchantUpdate",
    "MerchantResponse",
    "MerchantLoginRequest",
    "MerchantLoginResponse",

    # Token schemas
    "Token",
    "TokenData",

    # TrustScore schemas
    "TrustScoreMetrics",
    "TrustScoreBase",
    "TrustScoreResponse",
    "TrustScoreCalculateResponse",
    "TrustScoreHistoryItem",
    "TrustScoreHistoryResponse",

    # Document schemas
    "DocumentType",
    "VerificationStatus",
    "DocumentUploadResponse",
    "DocumentVerificationResult",
    "DocumentResponse",
    "DocumentListResponse",

    # Badge schemas
    "BadgeGenerateResponse",
    "BadgeResponse",
    "BadgeVerificationResponse",
    "BadgeShareInfo",
]
