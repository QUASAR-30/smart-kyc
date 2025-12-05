"""
SmartKYC - Badge Generator Service
Generates visual badge images for different TrustScore levels
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class BadgeGenerator:
    """
    Badge image generator for TrustScore levels.

    Creates visual badges with merchant name, TrustScore, and badge level.
    """

    # Badge level colors (RGB)
    BADGE_COLORS = {
        'PLATINUM': {
            'primary': (229, 228, 226),      # Platinum gray
            'secondary': (189, 195, 199),    # Light gray
            'text': (44, 62, 80),            # Dark gray
            'accent': (149, 165, 166)        # Medium gray
        },
        'GOLD': {
            'primary': (255, 215, 0),        # Gold
            'secondary': (255, 235, 59),     # Light gold
            'text': (33, 33, 33),            # Almost black
            'accent': (255, 193, 7)          # Amber
        },
        'SILVER': {
            'primary': (192, 192, 192),      # Silver
            'secondary': (211, 211, 211),    # Light gray
            'text': (33, 33, 33),            # Almost black
            'accent': (169, 169, 169)        # Dark gray
        },
        'BRONZE': {
            'primary': (205, 127, 50),       # Bronze
            'secondary': (244, 164, 96),     # Sandy brown
            'text': (33, 33, 33),            # Almost black
            'accent': (184, 115, 51)         # Peru
        },
        'NONE': {
            'primary': (189, 189, 189),      # Gray
            'secondary': (224, 224, 224),    # Light gray
            'text': (97, 97, 97),            # Dark gray
            'accent': (158, 158, 158)        # Medium gray
        }
    }

    # Badge dimensions
    BADGE_WIDTH = 600
    BADGE_HEIGHT = 400

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize badge generator.

        Args:
            output_dir: Directory to save badge images (default: backend/data/badges/)
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL (Pillow) not available. Install with: pip install pillow")

        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("/home/quasars/Documents/smartkyc-hackathon/smartkyc/backend/data/badges")

        # Create directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_badge(
        self,
        badge_level: str,
        trustscore: int,
        business_name: str,
        merchant_id: Optional[str] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a badge image.

        Args:
            badge_level: Badge level (BRONZE, SILVER, GOLD, PLATINUM, NONE)
            trustscore: TrustScore value (0-1000)
            business_name: Name of the business
            merchant_id: Optional merchant ID for organizing files
            filename: Optional custom filename

        Returns:
            Path to saved badge image

        Example:
            generator = BadgeGenerator()
            badge_path = generator.generate_badge("GOLD", 850, "Kouassi Distribution")
        """
        # Validate badge level
        if badge_level not in self.BADGE_COLORS:
            badge_level = 'NONE'

        colors = self.BADGE_COLORS[badge_level]

        # Create image with gradient background
        img = self._create_gradient_background(colors['primary'], colors['secondary'])
        draw = ImageDraw.Draw(img)

        # Load fonts
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            score_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
            name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
            label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except Exception:
            # Fallback to default font
            title_font = ImageFont.load_default()
            score_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            label_font = ImageFont.load_default()

        # Draw badge level title
        title_text = f"{badge_level} BADGE"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.BADGE_WIDTH - title_width) // 2
        draw.text((title_x, 30), title_text, fill=colors['text'], font=title_font)

        # Draw decorative line
        line_y = 100
        draw.rectangle(
            [(50, line_y), (self.BADGE_WIDTH - 50, line_y + 3)],
            fill=colors['accent']
        )

        # Draw TrustScore
        score_text = f"{trustscore}"
        score_bbox = draw.textbbox((0, 0), score_text, font=score_font)
        score_width = score_bbox[2] - score_bbox[0]
        score_x = (self.BADGE_WIDTH - score_width) // 2
        draw.text((score_x, 130), score_text, fill=colors['text'], font=score_font)

        # Draw "/1000" label
        max_label = "/1000"
        max_bbox = draw.textbbox((0, 0), max_label, font=name_font)
        max_width = max_bbox[2] - max_bbox[0]
        max_x = (self.BADGE_WIDTH - max_width) // 2
        draw.text((max_x, 210), max_label, fill=colors['accent'], font=name_font)

        # Draw business name (truncate if too long)
        max_name_length = 35
        display_name = business_name[:max_name_length] + "..." if len(business_name) > max_name_length else business_name
        name_bbox = draw.textbbox((0, 0), display_name, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = (self.BADGE_WIDTH - name_width) // 2
        draw.text((name_x, 260), display_name, fill=colors['text'], font=name_font)

        # Draw year and "SmartKYC" branding
        current_year = datetime.now().year
        footer_text = f"SmartKYC {current_year}"
        footer_bbox = draw.textbbox((0, 0), footer_text, font=label_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        footer_x = (self.BADGE_WIDTH - footer_width) // 2
        draw.text((footer_x, 330), footer_text, fill=colors['accent'], font=label_font)

        # Draw "Le Badge de Confiance du B2B Africain"
        tagline = "Le Badge de Confiance du B2B Africain"
        tagline_bbox = draw.textbbox((0, 0), tagline, font=label_font)
        tagline_width = tagline_bbox[2] - tagline_bbox[0]
        tagline_x = (self.BADGE_WIDTH - tagline_width) // 2
        draw.text((tagline_x, 360), tagline, fill=colors['accent'], font=label_font)

        # Determine output path
        if merchant_id:
            merchant_dir = self.output_dir / merchant_id
            merchant_dir.mkdir(parents=True, exist_ok=True)
            output_path = merchant_dir / (filename or f"badge_{badge_level.lower()}_{trustscore}.png")
        else:
            output_path = self.output_dir / (filename or f"badge_{badge_level.lower()}_{trustscore}.png")

        # Save image
        img.save(str(output_path), quality=95)

        return str(output_path)

    def _create_gradient_background(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> Image.Image:
        """
        Create a vertical gradient background.

        Args:
            color1: Start color (RGB tuple)
            color2: End color (RGB tuple)

        Returns:
            PIL Image with gradient background
        """
        img = Image.new('RGB', (self.BADGE_WIDTH, self.BADGE_HEIGHT), color1)
        draw = ImageDraw.Draw(img)

        # Draw gradient
        for y in range(self.BADGE_HEIGHT):
            # Calculate interpolation ratio
            ratio = y / self.BADGE_HEIGHT

            # Interpolate colors
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)

            # Draw horizontal line
            draw.line([(0, y), (self.BADGE_WIDTH, y)], fill=(r, g, b))

        return img

    def generate_badge_with_qr(
        self,
        badge_level: str,
        trustscore: int,
        business_name: str,
        qr_code_path: str,
        merchant_id: Optional[str] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a badge image with embedded QR code.

        Args:
            badge_level: Badge level
            trustscore: TrustScore value
            business_name: Name of the business
            qr_code_path: Path to QR code image
            merchant_id: Optional merchant ID
            filename: Optional custom filename

        Returns:
            Path to saved badge image with QR code
        """
        # Generate base badge first
        temp_filename = "temp_badge.png"
        base_badge_path = self.generate_badge(
            badge_level, trustscore, business_name, merchant_id, temp_filename
        )

        # Open badge image
        badge_img = Image.open(base_badge_path)

        # Open and resize QR code
        if os.path.exists(qr_code_path):
            qr_img = Image.open(qr_code_path)
            qr_size = 120  # Small QR code in corner
            qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

            # Position QR code in bottom right corner
            qr_x = self.BADGE_WIDTH - qr_size - 20
            qr_y = self.BADGE_HEIGHT - qr_size - 20

            # Paste QR code onto badge
            badge_img.paste(qr_img, (qr_x, qr_y))

        # Determine final output path
        if merchant_id:
            merchant_dir = self.output_dir / merchant_id
            merchant_dir.mkdir(parents=True, exist_ok=True)
            output_path = merchant_dir / (filename or f"badge_qr_{badge_level.lower()}_{trustscore}.png")
        else:
            output_path = self.output_dir / (filename or f"badge_qr_{badge_level.lower()}_{trustscore}.png")

        # Save final image
        badge_img.save(str(output_path), quality=95)

        # Clean up temp file
        if os.path.exists(base_badge_path):
            os.remove(base_badge_path)

        return str(output_path)


# Convenience function
def generate_badge(badge_level: str, trustscore: int, business_name: str, merchant_id: Optional[str] = None) -> str:
    """
    Convenience function to generate a badge.

    Args:
        badge_level: Badge level (BRONZE, SILVER, GOLD, PLATINUM, NONE)
        trustscore: TrustScore value (0-1000)
        business_name: Name of the business
        merchant_id: Optional merchant ID

    Returns:
        Path to saved badge image
    """
    generator = BadgeGenerator()
    return generator.generate_badge(badge_level, trustscore, business_name, merchant_id)
