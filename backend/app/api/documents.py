"""
SmartKYC - Documents API
Document upload and verification endpoints
"""

import os
import uuid
import json
from pathlib import Path
from typing import List
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Merchant, Document as DocumentModel, DocumentType as DocumentTypeEnum, VerificationStatus as VerificationStatusEnum
from app.schemas import DocumentUploadResponse, DocumentResponse, DocumentListResponse, DocumentType
from app.api.auth import get_current_merchant
from app.services.document_verifier import verify_document


router = APIRouter()

# Upload directory
UPLOAD_DIR = Path("/home/quasars/Documents/smartkyc-hackathon/smartkyc/backend/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Upload and verify a document.

    Steps:
    1. Validate file (extension, size)
    2. Save file to disk
    3. Run OCR verification immediately
    4. Save document record to database
    5. Return verification result

    Args:
        file: Uploaded file (JPG, PNG, PDF)
        document_type: Type of document (RCCM, CNI, NIF, etc.)
        merchant: Authenticated merchant (from JWT)
        db: Database session

    Returns:
        DocumentUploadResponse with verification results
    """
    # Validate file extension
    print("1")
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    print("2")
    # Read file content
    content = await file.read()
    file_size = len(content)
    print("3")
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    print("4")
    # Create merchant-specific directory
    merchant_dir = UPLOAD_DIR / merchant.id / document_type.value
    merchant_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{document_type.value}_{timestamp}_{uuid.uuid4().hex[:8]}{file_ext}"
    filepath = merchant_dir / unique_filename
    print("5")
    # Save file to disk
    try:
        with open(filepath, "wb") as f:
            f.write(content)
            print("6")
    except Exception as e:
        print("7")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            
            detail=f"Failed to save file: {str(e)}"
        )
        
    print("8")
    # Run OCR verification immediately
    verification_result = verify_document(
        filepath=str(filepath),
        document_type=document_type.value,
        merchant_id=merchant.id
    )

    # Map verification status to enum
    verification_status = VerificationStatusEnum[verification_result['status']]

    # Create document record in database
    document = DocumentModel(
        id=str(uuid.uuid4()),
        merchant_id=merchant.id,
        document_type=DocumentTypeEnum[document_type.value],
        filename=unique_filename,
        filepath=str(filepath),
        file_size=file_size,
        verification_status=verification_status,
        verified_at=datetime.utcnow() if verification_status == VerificationStatusEnum.VERIFIED else None,
        extracted_data=json.dumps(verification_result.get('extracted_data', {})),
        uploaded_at=datetime.utcnow()
    )
    document_type_str = document_type.value  # ex. "RCCM"

    # Supprime l'ancien document
    db.query(DocumentModel).filter(
        DocumentModel.merchant_id == merchant.id,          # ✅ merchant.id, pas merchant_id non défini
        DocumentModel.document_type == document_type_str   # ✅ chaîne pure
    ).delete()

    db.add(document)
    db.commit()
    db.refresh(document)

    # Build response
    return DocumentUploadResponse(
        id=document.id,
        merchant_id=document.merchant_id,
        document_type=document.document_type.value,
        filename=document.filename,
        file_size=document.file_size,
        verification_status=document.verification_status.value,
        uploaded_at=document.uploaded_at.isoformat(),
        verified_at=document.verified_at.isoformat() if document.verified_at else None,
        extracted_data=verification_result.get('extracted_data'),
        verification_reason=verification_result.get('reason'),
        confidence=verification_result.get('confidence', 0.0)
    )


@router.get("/list", response_model=DocumentListResponse)
def list_documents(
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    List all documents for the authenticated merchant.

    Returns:
        List of all uploaded documents with their verification status
    """
    documents = db.query(DocumentModel)\
        .filter(DocumentModel.merchant_id == merchant.id)\
        .order_by(DocumentModel.uploaded_at.desc())\
        .all()

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                merchant_id=doc.merchant_id,
                document_type=doc.document_type.value,
                filename=doc.filename,
                filepath=doc.filepath,
                file_size=doc.file_size,
                verification_status=doc.verification_status.value,
                verified_at=doc.verified_at,
                extracted_data=doc.extracted_data,
                uploaded_at=doc.uploaded_at
            )
            for doc in documents
        ],
        total=len(documents)
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID.

    Args:
        document_id: Document UUID
        merchant: Authenticated merchant
        db: Database session

    Returns:
        Document details with verification status
    """
    document = db.query(DocumentModel)\
        .filter(DocumentModel.id == document_id)\
        .filter(DocumentModel.merchant_id == merchant.id)\
        .first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return DocumentResponse(
        id=document.id,
        merchant_id=document.merchant_id,
        document_type=document.document_type.value,
        filename=document.filename,
        filepath=document.filepath,
        file_size=document.file_size,
        verification_status=document.verification_status.value,
        verified_at=document.verified_at,
        extracted_data=document.extracted_data,
        uploaded_at=document.uploaded_at
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """
    Delete a document.

    Args:
        document_id: Document UUID
        merchant: Authenticated merchant
        db: Database session

    Returns:
        204 No Content on success
    """
    document = db.query(DocumentModel)\
        .filter(DocumentModel.id == document_id)\
        .filter(DocumentModel.merchant_id == merchant.id)\
        .first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Delete file from disk
    try:
        if os.path.exists(document.filepath):
            os.remove(document.filepath)
    except Exception as e:
        print(f"⚠️  Failed to delete file {document.filepath}: {e}")

    # Delete from database
    db.delete(document)
    db.commit()

    return None
