"""
SmartKYC - Merchant Model
SQLAlchemy model for merchants table
"""

from datetime import datetime
from typing import List
import enum

from sqlalchemy import String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SubscriptionTier(str, enum.Enum):
    """Subscription tier enumeration"""
    FREE = "FREE"
    BASIC = "BASIC"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class Merchant(Base):
    """
    Merchant model representing business accounts.

    Attributes:
        id: Unique merchant identifier (UUID)
        genuka_merchant_id: Genuka platform merchant ID
        email: Merchant email (unique)
        business_name: Business name
        access_token: OAuth access token for Genuka API
        token_expires_at: Token expiration timestamp
        subscription_tier: Subscription level (FREE, BASIC, PRO, ENTERPRISE)
        subscription_ends_at: Subscription end date
        created_at: Account creation timestamp
        updated_at: Last update timestamp

    Relationships:
        trustscores: List of TrustScore calculations
        documents: List of uploaded documents
        badge: Badge information (one-to-one)
        verifications: List of badge verifications
    """

    __tablename__ = "merchants"

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Genuka Integration
    genuka_merchant_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True
    )

    # Account Information
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # OAuth Tokens
    access_token: Mapped[str] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Subscription
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        SQLEnum(SubscriptionTier),
        nullable=False,
        default=SubscriptionTier.FREE
    )
    subscription_ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    trustscores: Mapped[List["TrustScore"]] = relationship(
        "TrustScore",
        back_populates="merchant",
        cascade="all, delete-orphan"
    )

    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="merchant",
        cascade="all, delete-orphan"
    )

    badge: Mapped["Badge"] = relationship(
        "Badge",
        back_populates="merchant",
        uselist=False,
        cascade="all, delete-orphan"
    )

    verifications: Mapped[List["Verification"]] = relationship(
        "Verification",
        back_populates="merchant",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Merchant(id={self.id}, email={self.email}, business_name={self.business_name})>"

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "genuka_merchant_id": self.genuka_merchant_id,
            "email": self.email,
            "business_name": self.business_name,
            "subscription_tier": self.subscription_tier.value,
            "subscription_ends_at": self.subscription_ends_at.isoformat() if self.subscription_ends_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
