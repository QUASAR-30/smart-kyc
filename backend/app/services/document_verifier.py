"""
SmartKYC - Document Verifier Service
OCR-based document verification for RCCM, CNI, NIF, etc.
"""

import os
import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class DocumentVerifier:
    """
    Document verification service using OCR and pattern matching.

    Note: For hackathon - no OHADA API access, using format validation only.
    """

    # Regex patterns for document validation
    RCCM_PATTERNS = [
        r'RC[/\s]?[A-Z]{2,3}[/\s]?\d{4,}[/\s]?[A-Z]\d*',  # RC/DLA/2023/A123
        r'RCCM[/\s]?\d{4,}',                                # RCCM 2023/123
        r'Registre\s+de\s+Commerce',                        # Full name
    ]

    NIF_PATTERNS = [
        r'M\d{12,15}',              # M + 12-15 digits
        r'NIF[:\s]+M\d{12,15}',     # NIF: M123...
        r'Numéro\s+d\'Identification\s+Fiscale',
    ]

    CNI_PATTERNS = [
        r'REPUBLIQUE',
        r'CAMEROUN',
        r'CARTE\s+NATIONALE',
        r'IDENTITE',
        r'\d{9,12}',  # CNI number (9-12 digits)
    ]

    BANK_STATEMENT_PATTERNS = [
        r'RELEVE\s+BANCAIRE',
        r'BANK\s+STATEMENT',
        r'COMPTE\s+N[°O]',
        r'SOLDE',
        r'DEBIT',
        r'CREDIT',
    ]

    ADDRESS_PROOF_PATTERNS = [
        r'FACTURE',
        r'BILL',
        r'ENEO',
        r'CAMWATER',
        r'ADRESSE',
        r'ADDRESS',
    ]

    def __init__(self):
        """Initialize document verifier."""
        if not TESSERACT_AVAILABLE:
            print("⚠️  WARNING: pytesseract or PIL not available. Install with: pip install pytesseract pillow")

    def verify_document(
        self,
        filepath: str,
        document_type: str,
        merchant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify a document using OCR and pattern matching.

        Args:
            filepath: Path to the uploaded document image
            document_type: Type of document (RCCM, CNI, NIF, etc.)
            merchant_id: Optional merchant ID for logging

        Returns:
            Dict with:
                - status: 'VERIFIED', 'REJECTED', or 'PENDING'
                - extracted_data: Dict of extracted information
                - reason: String explaining the result
                - confidence: Float 0-100 (OCR confidence)
        """
        # Validate file exists
        if not os.path.exists(filepath):
            return {
                'status': 'REJECTED',
                'extracted_data': {},
                'reason': 'File not found',
                'confidence': 0.0
            }

        # Extract text using OCR
        extracted_text, confidence = self._extract_text_from_image(filepath)

        if not extracted_text:
            return {
                'status': 'REJECTED',
                'extracted_data': {},
                'reason': 'Could not extract text from image (may be blurry or invalid format)',
                'confidence': confidence
            }

        # Verify based on document type
        if document_type == 'RCCM':
            result = self._verify_rccm(extracted_text, filepath)
        elif document_type == 'NIF':
            result = self._verify_nif(extracted_text, filepath)
        elif document_type == 'CNI':
            result = self._verify_cni(extracted_text, filepath)
        elif document_type == 'BANK_STATEMENT':
            result = self._verify_bank_statement(extracted_text, filepath)
        elif document_type == 'ADDRESS_PROOF':
            result = self._verify_address_proof(extracted_text, filepath)
        else:
            return {
                'status': 'REJECTED',
                'extracted_data': {},
                'reason': f'Unknown document type: {document_type}',
                'confidence': 0.0
            }

        # Add confidence to result
        result['confidence'] = confidence
        result['extracted_text_preview'] = extracted_text[:200] if extracted_text else ''

        return result

    def _extract_text_from_image(self, filepath: str) -> Tuple[str, float]:
        """
        Extract text from image using Tesseract OCR.

        Args:
            filepath: Path to image file

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        if not TESSERACT_AVAILABLE:
            return '', 0.0

        try:
            # Open image
            image = Image.open(filepath)

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Extract text with French language support
            custom_config = r'--oem 3 --psm 6 -l fra+eng'
            extracted_text = pytesseract.image_to_string(image, config=custom_config)

            # Get confidence score
            try:
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=custom_config)
                confidences = [int(conf) for conf in data['conf'] if conf != '-1']
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            except Exception:
                avg_confidence = 70.0  # Default confidence if extraction fails

            return extracted_text.strip(), avg_confidence

        except Exception as e:
            print(f"❌ OCR Error: {e}")
            return '', 0.0

    def _verify_rccm(self, text: str, filepath: str) -> Dict[str, Any]:
        """
        Verify RCCM (Registre de Commerce) document.

        Looks for:
        - RC/DLA/2023/A123 format
        - RCCM number
        - Company name
        - Registration date
        """
        text_upper = text.upper()

        extracted_data = {}
        matches_found = 0

        # Search for RCCM number
        for pattern in self.RCCM_PATTERNS:
            matches = re.findall(pattern, text_upper)
            if matches:
                extracted_data['rccm_number'] = matches[0]
                matches_found += 1
                break

        # Extract company name (heuristic: look for capital words after "DENOMINATION" or "RAISON SOCIALE")
        company_patterns = [
            r'DENOMINATION[:\s]+([A-Z][A-Z\s]{5,50})',
            r'RAISON\s+SOCIALE[:\s]+([A-Z][A-Z\s]{5,50})',
            r'NOM\s+COMMERCIAL[:\s]+([A-Z][A-Z\s]{5,50})',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, text_upper)
            if match:
                extracted_data['company_name'] = match.group(1).strip()
                matches_found += 1
                break

        # Extract registration date
        date_patterns = [
            r'DATE[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'(\d{1,2}\s+[A-Z]{3,9}\s+\d{4})',  # 15 Mars 2023
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text_upper)
            if match:
                extracted_data['registration_date'] = match.group(1)
                matches_found += 1
                break

        # Decision based on matches
        if matches_found >= 1:
            # At least RCCM number or company name found
            status = 'VERIFIED'
            reason = f'RCCM document verified with {matches_found} matching field(s)'
        else:
            status = 'REJECTED'
            reason = 'No RCCM patterns found in document'

        return {
            'status': status,
            'extracted_data': extracted_data,
            'reason': reason
        }

    def _verify_nif(self, text: str, filepath: str) -> Dict[str, Any]:
        """
        Verify NIF (Numéro d'Identification Fiscale) document.

        Format: M + 12-15 digits (e.g., M123456789012)
        """
        text_upper = text.upper()

        extracted_data = {}
        matches_found = 0

        # Search for NIF number
        for pattern in self.NIF_PATTERNS:
            matches = re.findall(pattern, text_upper)
            if matches:
                # Extract just the M+digits part
                nif_match = re.search(r'M\d{12,15}', matches[0])
                if nif_match:
                    extracted_data['nif_number'] = nif_match.group(0)
                    matches_found += 1
                    break

        # Extract taxpayer name
        name_patterns = [
            r'NOM[:\s]+([A-Z][A-Z\s]{5,50})',
            r'CONTRIBUABLE[:\s]+([A-Z][A-Z\s]{5,50})',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text_upper)
            if match:
                extracted_data['taxpayer_name'] = match.group(1).strip()
                matches_found += 1
                break

        # Decision
        if 'nif_number' in extracted_data:
            status = 'VERIFIED'
            reason = f'NIF verified: {extracted_data["nif_number"]}'
        elif matches_found >= 1:
            status = 'PENDING'
            reason = 'NIF keywords found but number not extracted clearly'
        else:
            status = 'REJECTED'
            reason = 'No NIF number found in document'

        return {
            'status': status,
            'extracted_data': extracted_data,
            'reason': reason
        }

    def _verify_cni(self, text: str, filepath: str) -> Dict[str, Any]:
        """
        Verify CNI (Carte Nationale d'Identité) document.

        Looks for:
        - REPUBLIQUE DU CAMEROUN
        - CARTE NATIONALE D'IDENTITE
        - CNI number (9-12 digits)
        - Name, birth date
        """
        text_upper = text.upper()

        extracted_data = {}
        matches_found = 0

        # Check for key CNI keywords
        for pattern in self.CNI_PATTERNS:
            if re.search(pattern, text_upper):
                matches_found += 1

        # Extract CNI number (usually 9-12 digits)
        cni_number_pattern = r'\b(\d{9,12})\b'
        cni_matches = re.findall(cni_number_pattern, text_upper)
        if cni_matches:
            # Take the longest number (likely the CNI number)
            extracted_data['cni_number'] = max(cni_matches, key=len)

        # Extract name (heuristic: look for NOM or NAME)
        name_patterns = [
            r'NOM[:\s]+([A-Z][A-Z\s]{5,50})',
            r'NAME[:\s]+([A-Z][A-Z\s]{5,50})',
            r'PRENOM[:\s]+([A-Z][A-Z\s]{5,50})',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text_upper)
            if match:
                extracted_data['holder_name'] = match.group(1).strip()
                break

        # Extract birth date
        date_patterns = [
            r'NE\s+LE[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'DATE\s+DE\s+NAISSANCE[:\s]+(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text_upper)
            if match:
                extracted_data['birth_date'] = match.group(1)
                break

        # Decision
        if matches_found >= 3:
            # At least 3 CNI keywords found
            status = 'VERIFIED'
            reason = f'CNI verified with {matches_found} matching keywords'
        elif matches_found >= 1:
            status = 'PENDING'
            reason = 'Some CNI keywords found, manual review recommended'
        else:
            status = 'REJECTED'
            reason = 'Document does not appear to be a valid CNI'

        return {
            'status': status,
            'extracted_data': extracted_data,
            'reason': reason
        }

    def _verify_bank_statement(self, text: str, filepath: str) -> Dict[str, Any]:
        """
        Verify bank statement document.

        Looks for typical bank statement keywords and account information.
        """
        text_upper = text.upper()

        extracted_data = {}
        matches_found = 0

        # Check for bank statement keywords
        for pattern in self.BANK_STATEMENT_PATTERNS:
            if re.search(pattern, text_upper):
                matches_found += 1

        # Extract account number
        account_patterns = [
            r'COMPTE\s+N[°O:]\s*(\d{10,20})',
            r'ACCOUNT\s+NUMBER[:\s]+(\d{10,20})',
        ]
        for pattern in account_patterns:
            match = re.search(pattern, text_upper)
            if match:
                extracted_data['account_number'] = match.group(1)
                break

        # Extract bank name
        bank_patterns = [
            r'(AFRILAND|BICEC|ECOBANK|UBA|SCB|SGBC)',
        ]
        for pattern in bank_patterns:
            match = re.search(pattern, text_upper)
            if match:
                extracted_data['bank_name'] = match.group(1)
                break

        # Decision
        if matches_found >= 3:
            status = 'VERIFIED'
            reason = f'Bank statement verified with {matches_found} matching fields'
        elif matches_found >= 1:
            status = 'PENDING'
            reason = 'Partial bank statement information found'
        else:
            status = 'REJECTED'
            reason = 'Document does not appear to be a bank statement'

        return {
            'status': status,
            'extracted_data': extracted_data,
            'reason': reason
        }

    def _verify_address_proof(self, text: str, filepath: str) -> Dict[str, Any]:
        """
        Verify address proof document (utility bill, etc.).

        Looks for typical utility bill keywords and address information.
        """
        text_upper = text.upper()

        extracted_data = {}
        matches_found = 0

        # Check for address proof keywords
        for pattern in self.ADDRESS_PROOF_PATTERNS:
            if re.search(pattern, text_upper):
                matches_found += 1

        # Extract address (heuristic)
        address_patterns = [
            r'ADRESSE[:\s]+([A-Z0-9][A-Z0-9\s,\.]{10,100})',
            r'ADDRESS[:\s]+([A-Z0-9][A-Z0-9\s,\.]{10,100})',
        ]
        for pattern in address_patterns:
            match = re.search(pattern, text_upper)
            if match:
                extracted_data['address'] = match.group(1).strip()
                break

        # Extract utility company
        if 'ENEO' in text_upper:
            extracted_data['utility_company'] = 'ENEO'
        elif 'CAMWATER' in text_upper:
            extracted_data['utility_company'] = 'CAMWATER'

        # Decision
        if matches_found >= 2:
            status = 'VERIFIED'
            reason = f'Address proof verified with {matches_found} matching fields'
        elif matches_found >= 1:
            status = 'PENDING'
            reason = 'Partial address information found'
        else:
            status = 'REJECTED'
            reason = 'Document does not appear to be valid address proof'

        return {
            'status': status,
            'extracted_data': extracted_data,
            'reason': reason
        }


# Convenience function
def verify_document(filepath: str, document_type: str, merchant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to verify a document.

    Args:
        filepath: Path to the document image
        document_type: Type of document (RCCM, CNI, NIF, BANK_STATEMENT, ADDRESS_PROOF)
        merchant_id: Optional merchant ID

    Returns:
        Verification result dictionary
    """
    verifier = DocumentVerifier()
    return verifier.verify_document(filepath, document_type, merchant_id)
