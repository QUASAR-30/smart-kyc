# Document Verification System - Setup Guide

## ✅ Implementation Complete

The document verification system is now fully implemented with:

- **OCR Service** ([document_verifier.py](app/services/document_verifier.py))
- **API Endpoints** ([documents.py](app/api/documents.py))
- **Database Integration** (Document model with verification status)
- **5 Document Types Support**: RCCM, NIF, CNI, BANK_STATEMENT, ADDRESS_PROOF

## 🔧 Installation Requirements

### 1. Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Verify installation:**
```bash
tesseract --version
# Should show: tesseract 4.x.x or higher
```

### 2. Python Dependencies

Already in [requirements.txt](requirements.txt):
```
pytesseract==0.3.10
Pillow==10.2.0
```

Install if needed:
```bash
pip install pytesseract pillow
```

## 📡 API Endpoints

### POST /api/documents/upload

Upload and verify a document with immediate OCR processing.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/rccm.jpg" \
  -F "document_type=RCCM"
```

**Response:**
```json
{
  "id": "abc-123-def",
  "merchant_id": "merchant-xyz",
  "document_type": "RCCM",
  "filename": "RCCM_20231205_abc123.jpg",
  "file_size": 245678,
  "verification_status": "VERIFIED",
  "uploaded_at": "2023-12-05T10:30:00",
  "verified_at": "2023-12-05T10:30:02",
  "extracted_data": {
    "rccm_number": "RC/DLA/2023/A/1234",
    "company_name": "KOUASSI DISTRIBUTION SARL",
    "registration_date": "15/03/2023"
  },
  "verification_reason": "RCCM document verified with 3 matching field(s)",
  "confidence": 87.5
}
```

### GET /api/documents/list

List all documents for authenticated merchant.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/documents/list" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "documents": [
    {
      "id": "abc-123",
      "document_type": "RCCM",
      "verification_status": "VERIFIED",
      "uploaded_at": "2023-12-05T10:30:00"
    }
  ],
  "total": 1
}
```

### GET /api/documents/{document_id}

Get specific document details.

### DELETE /api/documents/{document_id}

Delete a document (removes file and database record).

## 🔍 Document Verification Logic

### RCCM (Registre de Commerce)
**Patterns searched:**
- `RC/DLA/2023/A/1234` format
- `RCCM` keyword
- Company name after "DENOMINATION" or "RAISON SOCIALE"
- Registration date

**Status:**
- `VERIFIED`: RCCM number + company name found
- `REJECTED`: No matching patterns

### NIF (Numéro d'Identification Fiscale)
**Patterns searched:**
- `M` + 12-15 digits (e.g., `M123456789012345`)
- Taxpayer name

**Status:**
- `VERIFIED`: Valid NIF number extracted
- `PENDING`: NIF keywords found but number unclear
- `REJECTED`: No NIF number found

### CNI (Carte Nationale d'Identité)
**Patterns searched:**
- Keywords: REPUBLIQUE, CAMEROUN, CARTE NATIONALE, IDENTITE
- CNI number (9-12 digits)
- Holder name, birth date

**Status:**
- `VERIFIED`: 3+ keywords found
- `PENDING`: 1-2 keywords found
- `REJECTED`: No CNI patterns

### Bank Statement
**Patterns searched:**
- Keywords: RELEVE BANCAIRE, COMPTE, SOLDE, DEBIT, CREDIT
- Account number
- Bank name (AFRILAND, BICEC, ECOBANK, etc.)

### Address Proof
**Patterns searched:**
- Keywords: FACTURE, ADRESSE, ENEO, CAMWATER
- Address text
- Utility company name

## 📂 File Storage

Documents are stored in:
```
backend/data/uploads/
  ├── {merchant_id}/
  │   ├── RCCM/
  │   │   └── RCCM_20231205_abc123.jpg
  │   ├── CNI/
  │   ├── NIF/
  │   ├── BANK_STATEMENT/
  │   └── ADDRESS_PROOF/
```

**Validation:**
- Allowed extensions: `.jpg`, `.jpeg`, `.png`, `.pdf`
- Max file size: 5MB
- Files stored with unique timestamp + UUID filename

## 🧪 Testing

Run the test suite:
```bash
cd /home/quasars/Documents/smartkyc-hackathon/smartkyc/backend
python3 test_document_api.py
```

**Tests cover:**
1. ✅ RCCM verification with OCR
2. ✅ NIF verification with pattern matching
3. ✅ CNI verification with keyword detection
4. ✅ Database integration (save and retrieve)
5. ✅ All document types have handlers

**Results:**
```
Total: 5/5 tests passed
🎉 All tests passed! Document verification API is working!
```

## 🚀 Usage Flow

### 1. Login
```bash
curl -X POST "http://localhost:8000/auth/mock-login" \
  -H "Content-Type: application/json" \
  -d '{"email": "merchant@example.cm"}'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 2. Upload RCCM
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -F "file=@rccm.jpg" \
  -F "document_type=RCCM"
```

### 3. Upload CNI
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -F "file=@cni.jpg" \
  -F "document_type=CNI"
```

### 4. Upload NIF
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -F "file=@nif.jpg" \
  -F "document_type=NIF"
```

### 5. Calculate TrustScore
```bash
curl -X POST "http://localhost:8000/api/trustscores/calculate" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

TrustScore now includes:
- **Documents metric (10%)**: Based on verified documents count
- Verified RCCM, CNI, NIF → Higher score

## ⚠️ Important Notes

### OCR Accuracy
- Tesseract OCR accuracy: 70-90% (not 100%)
- For best results:
  - Use high-quality images (clear, well-lit)
  - Avoid blurry or skewed photos
  - Ensure text is readable

### Hackathon Mode
- No OHADA API integration (as specified in CLAUDE.md)
- Validation is format-based only
- For production: integrate with official registries

### Error Handling
- Invalid file type → 400 Bad Request
- File too large → 400 Bad Request
- OCR fails → Status "REJECTED" with reason
- Missing Tesseract → Graceful degradation (returns REJECTED)

## 📊 Database Schema

**documents table:**
```sql
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,
    merchant_id VARCHAR(36) NOT NULL,
    document_type ENUM('RCCM', 'CNI', 'NIF', 'BANK_STATEMENT', 'ADDRESS_PROOF'),
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(500) NOT NULL,
    file_size INT NOT NULL,
    verification_status ENUM('PENDING', 'VERIFIED', 'REJECTED'),
    verified_at DATETIME NULL,
    extracted_data TEXT NULL,  -- JSON
    uploaded_at DATETIME NOT NULL,
    FOREIGN KEY (merchant_id) REFERENCES merchants(id)
);
```

## 🎯 Next Steps

1. **For Development:**
   - Install Tesseract OCR
   - Test with real document images
   - Adjust regex patterns if needed for Cameroon formats

2. **For Production:**
   - Integrate OHADA API for RCCM validation
   - Add document expiration checks
   - Implement manual review queue for PENDING status
   - Add virus scanning for uploaded files

3. **For Hackathon Demo:**
   - Prepare 5 test documents (RCCM, CNI, NIF, Bank, Address)
   - Ensure images are clear and well-formatted
   - Test upload flow 10× before presentation

## 📞 Support

**Issues?**
- Check Tesseract installation: `tesseract --version`
- Check file permissions: `ls -la backend/data/uploads/`
- Check logs: SQLAlchemy prints all queries
- Test manually with [test_document_api.py](test_document_api.py)

**Files Created:**
- ✅ [app/services/document_verifier.py](app/services/document_verifier.py) - OCR service
- ✅ [app/schemas/document.py](app/schemas/document.py) - Pydantic schemas
- ✅ [app/api/documents.py](app/api/documents.py) - API endpoints
- ✅ [test_document_api.py](test_document_api.py) - Test suite

---

**Last Updated:** 2025-12-05
**Status:** ✅ Ready for Integration
