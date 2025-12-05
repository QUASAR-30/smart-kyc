"""
SmartKYC - Badge Model
SQLAlchemy model for badges table
"""

from datetime import datetime
import enum

from sqlalchemy import String, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class BadgeLevel(str, enum.Enum):
    """Badge level enumeration"""
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"


class Badge(Base):
    """
    Badge model representing merchant trust badges.

    Attributes:
        id: Unique badge identifier (UUID)
        merchant_id: Reference to merchant (one-to-one)
        badge_level: Badge level (BRONZE, SILVER, GOLD, PLATINUM)
        badge_image_path: Path to badge image file
        qr_code_data: QR code data content
        qr_code_image_path: Path to QR code image file
        verification_code: Unique verification code for public verification
        issued_at: Badge issuance timestamp
        expires_at: Badge expiration date (6 months)
        is_active: Badge active status

    Relationships:
        merchant: Associated merchant (one-to-one)
    """

    __tablename__ = "badges"

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Key (one-to-one with merchant)
    merchant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    # Badge Information
    badge_level: Mapped[BadgeLevel] = mapped_column(
        SQLEnum(BadgeLevel),
        nullable=False
    )
    badge_image_path: Mapped[str] = mapped_column(String(500), nullable=True)

    # QR Code
    qr_code_data: Mapped[str] = mapped_column(Text, nullable=False)
    qr_code_image_path: Mapped[str] = mapped_column(String(500), nullable=True)
    verification_code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # Validity
    issued_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="badge"
    )

    def __repr__(self) -> str:
        return (f"<Badge(id={self.id}, merchant_id={self.merchant_id}, "
                f"level={self.badge_level.value}, code={self.verification_code})>")

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "badge_level": self.badge_level.value,
            "badge_image_path": self.badge_image_path,
            "qr_code_data": self.qr_code_data,
            "qr_code_image_path": self.qr_code_image_path,
            "verification_code": self.verification_code,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_active": self.is_active
        }

    def is_valid(self) -> bool:
        """Check if badge is still valid (not expired and active)"""
        return self.is_active and datetime.utcnow() < self.expires_at

    def deactivate(self) -> None:
        """Deactivate the badge"""
        self.is_active = False

    def activate(self) -> None:
        """Activate the badge"""
        self.is_active = True
