"""
SmartKYC - TrustScore Model
SQLAlchemy model for trustscores table
"""

from datetime import datetime
import enum
import json

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class BadgeLevel(str, enum.Enum):
    """Badge level enumeration"""
    NONE = "NONE"
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"


class CalculationMode(str, enum.Enum):
    """TrustScore calculation mode enumeration"""
    COLD_START = "COLD_START"
    NORMAL = "NORMAL"


class TrustScore(Base):
    """
    TrustScore model representing merchant trust score calculations.

    Attributes:
        id: Unique TrustScore identifier (UUID)
        merchant_id: Reference to merchant
        trustscore: TrustScore value (0-1000)
        badge: Badge level (NONE, BRONZE, SILVER, GOLD, PLATINUM)
        metrics: JSON metrics breakdown
        calculation_mode: Mode used (COLD_START or NORMAL)
        valid_until: Score validity expiration date
        created_at: Calculation timestamp

    Relationships:
        merchant: Associated merchant (many-to-one)
    """

    __tablename__ = "trustscores"

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Key
    merchant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Score Information
    trustscore: Mapped[int] = mapped_column(Integer, nullable=False)
    badge: Mapped[BadgeLevel] = mapped_column(
        SQLEnum(BadgeLevel),
        nullable=False
    )

    # Metrics (JSON)
    metrics: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata
    calculation_mode: Mapped[CalculationMode] = mapped_column(
        SQLEnum(CalculationMode),
        nullable=False
    )
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="trustscores"
    )

    def __repr__(self) -> str:
        return (f"<TrustScore(id={self.id}, merchant_id={self.merchant_id}, "
                f"score={self.trustscore}, badge={self.badge.value})>")

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "trustscore": self.trustscore,
            "badge": self.badge.value,
            "metrics": json.loads(self.metrics) if isinstance(self.metrics, str) else self.metrics,
            "calculation_mode": self.calculation_mode.value,
            "valid_until": self.valid_until.isoformat(),
            "created_at": self.created_at.isoformat()
        }

    def get_metrics(self) -> dict:
        """Parse and return metrics as dictionary"""
        if isinstance(self.metrics, str):
            return json.loads(self.metrics)
        return self.metrics

    def set_metrics(self, metrics_dict: dict) -> None:
        """Set metrics from dictionary"""
        self.metrics = json.dumps(metrics_dict)
