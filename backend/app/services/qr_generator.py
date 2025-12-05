"""
SmartKYC - QR Code Generator Service
Generates QR codes for badge verification
"""

import os
from pathlib import Path
from typing import Optional

try:
    import qrcode
    from qrcode.image.pil import PilImage
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


class QRCodeGenerator:
    """
    QR Code generator for badge verification.

    Generates QR codes that link to the public verification page.
    """

    # Base URL for verification (can be changed for production)
    BASE_VERIFICATION_URL = "https://verify.smartkyc.cm/verify"

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize QR code generator.

        Args:
            output_dir: Directory to save QR code images (default: backend/data/qrcodes/)
        """
        if not QRCODE_AVAILABLE:
            raise ImportError("qrcode library not available. Install with: pip install qrcode[pil]")

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("/home/quasars/Documents/smartkyc-hackathon/smartkyc/backend/data/qrcodes")

        # Create directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_qr_code(
        self,
        verification_code: str,
        merchant_id: Optional[str] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a QR code for badge verification.

        Args:
            verification_code: Unique verification code (UUID)
            merchant_id: Optional merchant ID for organizing files
            filename: Optional custom filename (default: qr_{verification_code}.png)

        Returns:
            Path to saved QR code image

        Example:
            generator = QRCodeGenerator()
            qr_path = generator.generate_qr_code("abc-123-def")
            # QR code contains: https://verify.smartkyc.cm/verify/abc-123-def
        """
        # Build verification URL
        verification_url = f"{self.BASE_VERIFICATION_URL}/{verification_code}"

        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,  # Controls size (1-40, 1 is smallest)
            error_correction=qrcode.constants.ERROR_CORRECT_L,  # ~7% error correction
            box_size=10,  # Size of each box in pixels
            border=4,  # Border size (minimum is 4)
        )

        # Add data
        qr.add_data(verification_url)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Determine output path
        if merchant_id:
            merchant_dir = self.output_dir / merchant_id
            merchant_dir.mkdir(parents=True, exist_ok=True)
            output_path = merchant_dir / (filename or f"qr_{verification_code}.png")
        else:
            output_path = self.output_dir / (filename or f"qr_{verification_code}.png")

        # Save image
        img.save(str(output_path))

        return str(output_path)

    def generate_qr_code_with_logo(
        self,
        verification_code: str,
        logo_path: Optional[str] = None,
        merchant_id: Optional[str] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a QR code with embedded logo (advanced version).

        Args:
            verification_code: Unique verification code
            logo_path: Path to logo image to embed in center
            merchant_id: Optional merchant ID
            filename: Optional custom filename

        Returns:
            Path to saved QR code image with logo
        """
        from PIL import Image

        # Generate basic QR code first
        verification_url = f"{self.BASE_VERIFICATION_URL}/{verification_code}"

        # Use higher error correction for QR with logo
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # ~30% error correction (needed for logo)
            box_size=10,
            border=4,
        )

        qr.add_data(verification_url)
        qr.make(fit=True)

        # Create QR image
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

        # Add logo if provided
        if logo_path and os.path.exists(logo_path):
            logo = Image.open(logo_path)

            # Calculate logo size (should be ~1/5 of QR code)
            qr_width, qr_height = qr_img.size
            logo_size = min(qr_width, qr_height) // 5

            # Resize logo
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

            # Calculate position (center)
            logo_pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)

            # Paste logo onto QR code
            qr_img.paste(logo, logo_pos)

        # Determine output path
        if merchant_id:
            merchant_dir = self.output_dir / merchant_id
            merchant_dir.mkdir(parents=True, exist_ok=True)
            output_path = merchant_dir / (filename or f"qr_logo_{verification_code}.png")
        else:
            output_path = self.output_dir / (filename or f"qr_logo_{verification_code}.png")

        # Save image
        qr_img.save(str(output_path))

        return str(output_path)

    def set_verification_url(self, base_url: str):
        """
        Update the base verification URL.

        Args:
            base_url: New base URL (e.g., "https://smartkyc.cm/verify")
        """
        self.BASE_VERIFICATION_URL = base_url


# Convenience function
def generate_qr_code(verification_code: str, merchant_id: Optional[str] = None) -> str:
    """
    Convenience function to generate a QR code.

    Args:
        verification_code: Unique verification code
        merchant_id: Optional merchant ID

    Returns:
        Path to saved QR code image
    """
    generator = QRCodeGenerator()
    return generator.generate_qr_code(verification_code, merchant_id)
