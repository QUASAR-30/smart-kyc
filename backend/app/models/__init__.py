"""
SmartKYC - Database Models
SQLAlchemy ORM models for all database tables
"""

from app.models.base import Base
from app.models.merchant import Merchant, SubscriptionTier
from app.models.trustscore import TrustScore, BadgeLevel as TrustScoreBadgeLevel, CalculationMode
from app.models.document import Document, DocumentType, VerificationStatus
from app.models.badge import Badge, BadgeLevel
from app.models.verification import Verification
from app.models.genuka_data import GenukaOrder, GenukaCustomer

__all__ = [
    # Base
    "Base",

    # Models
    "Merchant",
    "TrustScore",
    "Document",
    "Badge",
    "Verification",
    "GenukaOrder",
    "GenukaCustomer",

    # Enums
    "SubscriptionTier",
    "TrustScoreBadgeLevel",
    "CalculationMode",
    "DocumentType",
    "VerificationStatus",
    "BadgeLevel",
]
