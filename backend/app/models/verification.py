"""
SmartKYC - Verification Model
SQLAlchemy model for verifications table
"""

from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Verification(Base):
    """
    Verification model for tracking badge verification views.

    Attributes:
        id: Unique verification identifier (UUID)
        merchant_id: Reference to merchant whose badge was viewed
        viewer_email: Email of person who viewed the badge (optional)
        viewer_ip: IP address of viewer
        viewed_at: Timestamp of verification view
        user_agent: Browser user agent string

    Relationships:
        merchant: Associated merchant (many-to-one)
    """

    __tablename__ = "verifications"

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Key
    merchant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Viewer Information
    viewer_email: Mapped[str] = mapped_column(String(255), nullable=True)
    viewer_ip: Mapped[str] = mapped_column(String(45), nullable=True)

    # Timestamp
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    # User Agent
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="verifications"
    )

    def __repr__(self) -> str:
        return (f"<Verification(id={self.id}, merchant_id={self.merchant_id}, "
                f"viewer_ip={self.viewer_ip}, viewed_at={self.viewed_at})>")

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "viewer_email": self.viewer_email,
            "viewer_ip": self.viewer_ip,
            "viewed_at": self.viewed_at.isoformat(),
            "user_agent": self.user_agent
        }
