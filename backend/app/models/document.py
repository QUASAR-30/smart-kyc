"""
SmartKYC - Document Model
SQLAlchemy model for documents table
"""

from datetime import datetime
import enum
import json

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DocumentType(str, enum.Enum):
    """Document type enumeration"""
    RCCM = "RCCM"
    CNI = "CNI"
    NIF = "NIF"
    BANK_STATEMENT = "BANK_STATEMENT"
    ADDRESS_PROOF = "ADDRESS_PROOF"


class VerificationStatus(str, enum.Enum):
    """Document verification status enumeration"""
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class Document(Base):
    """
    Document model representing uploaded merchant documents.

    Attributes:
        id: Unique document identifier (UUID)
        merchant_id: Reference to merchant
        document_type: Type of document (RCCM, CNI, NIF, etc.)
        filename: Original filename
        filepath: Storage file path
        file_size: File size in bytes
        verification_status: Verification status (PENDING, VERIFIED, REJECTED)
        verified_at: Verification completion timestamp
        extracted_data: OCR extracted data (JSON)
        uploaded_at: Upload timestamp

    Relationships:
        merchant: Associated merchant (many-to-one)
    """

    __tablename__ = "documents"

    # Primary Key
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Foreign Key
    merchant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Document Information
    document_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType),
        nullable=False,
        index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    # Verification
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SQLEnum(VerificationStatus),
        nullable=False,
        default=VerificationStatus.PENDING
    )
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # OCR Data (JSON)
    extracted_data: Mapped[str] = mapped_column(Text, nullable=True)

    # Timestamp
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # Relationships
    merchant: Mapped["Merchant"] = relationship(
        "Merchant",
        back_populates="documents"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            'merchant_id',
            'document_type',
            name='unique_merchant_doc'
        ),
    )

    def __repr__(self) -> str:
        return (f"<Document(id={self.id}, merchant_id={self.merchant_id}, "
                f"type={self.document_type.value}, status={self.verification_status.value})>")

    def to_dict(self) -> dict:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "merchant_id": self.merchant_id,
            "document_type": self.document_type.value,
            "filename": self.filename,
            "filepath": self.filepath,
            "file_size": self.file_size,
            "verification_status": self.verification_status.value,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "extracted_data": json.loads(self.extracted_data) if self.extracted_data else None,
            "uploaded_at": self.uploaded_at.isoformat()
        }

    def get_extracted_data(self) -> dict:
        """Parse and return extracted data as dictionary"""
        if self.extracted_data:
            if isinstance(self.extracted_data, str):
                return json.loads(self.extracted_data)
            return self.extracted_data
        return {}

    def set_extracted_data(self, data_dict: dict) -> None:
        """Set extracted data from dictionary"""
        self.extracted_data = json.dumps(data_dict)

    def mark_verified(self) -> None:
        """Mark document as verified"""
        self.verification_status = VerificationStatus.VERIFIED
        self.verified_at = datetime.utcnow()

    def mark_rejected(self) -> None:
        """Mark document as rejected"""
        self.verification_status = VerificationStatus.REJECTED
        self.verified_at = datetime.utcnow()
