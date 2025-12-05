"""
SmartKYC - Document Schemas
Pydantic schemas for document upload and verification
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class DocumentType(str, Enum):
    """Document type enum."""
    RCCM = "RCCM"
    CNI = "CNI"
    NIF = "NIF"
    BANK_STATEMENT = "BANK_STATEMENT"
    ADDRESS_PROOF = "ADDRESS_PROOF"


class VerificationStatus(str, Enum):
    """Document verification status enum."""
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class DocumentUploadResponse(BaseModel):
    """Response for document upload."""
    id: str
    merchant_id: str
    document_type: str
    filename: str
    file_size: int
    verification_status: str
    uploaded_at: str
    verified_at: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    verification_reason: Optional[str] = None
    confidence: Optional[float] = None

    class Config:
        from_attributes = True


class DocumentVerificationResult(BaseModel):
    """Result of document verification."""
    status: str = Field(..., description="VERIFIED, REJECTED, or PENDING")
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(..., description="Explanation of verification result")
    confidence: float = Field(0.0, description="OCR confidence score 0-100")
    extracted_text_preview: Optional[str] = None


class DocumentResponse(BaseModel):
    """Response for single document."""
    id: str
    merchant_id: str
    document_type: str
    filename: str
    filepath: str
    file_size: int
    verification_status: str
    verified_at: Optional[datetime] = None
    extracted_data: Optional[str] = None  # JSON string
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response for list of documents."""
    documents: list[DocumentResponse]
    total: int
