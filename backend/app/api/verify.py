"""
SmartKYC - Public Verification Page
Public endpoint for badge verification via QR code
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi import Depends

from app.database import get_db
from app.models import Badge, Merchant, TrustScore, Document, VerificationStatus


router = APIRouter()


def get_badge_color(badge_level: str) -> dict:
    """Get color scheme for badge level."""
    colors = {
        'PLATINUM': {
            'bg': 'linear-gradient(135deg, #E5E4E2 0%, #BDC3C7 100%)',
            'text': '#2C3E50',
            'border': '#95A5A6'
        },
        'GOLD': {
            'bg': 'linear-gradient(135deg, #FFD700 0%, #FFC107 100%)',
            'text': '#212121',
            'border': '#FFA000'
        },
        'SILVER': {
            'bg': 'linear-gradient(135deg, #C0C0C0 0%, #D3D3D3 100%)',
            'text': '#212121',
            'border': '#A9A9A9'
        },
        'BRONZE': {
            'bg': 'linear-gradient(135deg, #CD7F32 0%, #F4A460 100%)',
            'text': '#212121',
            'border': '#B87333'
        },
        'NONE': {
            'bg': 'linear-gradient(135deg, #BDBDBD 0%, #E0E0E0 100%)',
            'text': '#616161',
            'border': '#9E9E9E'
        }
    }
    return colors.get(badge_level, colors['NONE'])


def get_credit_recommendation(trustscore: int, badge_level: str) -> str:
    """Get credit recommendation based on TrustScore."""
    if trustscore >= 850 and badge_level == 'PLATINUM':
        return "💎 Crédit recommandé jusqu'à 2,000,000 FCFA"
    elif trustscore >= 700:
        return "🥇 Crédit recommandé jusqu'à 800,000 FCFA"
    elif trustscore >= 550:
        return "🥈 Crédit recommandé jusqu'à 400,000 FCFA"
    elif trustscore >= 400:
        return "🥉 Crédit recommandé jusqu'à 200,000 FCFA"
    else:
        return "⚠️ Crédit non recommandé - Score insuffisant"


def generate_verification_html(
    merchant_name: str,
    business_name: str,
    trustscore: int,
    badge_level: str,
    verified_documents: list,
    issued_at: datetime,
    expires_at: datetime,
    is_expired: bool
) -> str:
    """Generate HTML page for badge verification."""

    colors = get_badge_color(badge_level)
    credit_rec = get_credit_recommendation(trustscore, badge_level)

    # Document icons
    doc_icons = {
        'RCCM': '📋',
        'CNI': '🪪',
        'NIF': '🔢',
        'BANK_STATEMENT': '🏦',
        'ADDRESS_PROOF': '📍'
    }

    doc_names = {
        'RCCM': 'Registre de Commerce',
        'CNI': 'Carte Nationale d\'Identité',
        'NIF': 'Numéro d\'Identification Fiscale',
        'BANK_STATEMENT': 'Relevé Bancaire',
        'ADDRESS_PROOF': 'Justificatif de Domicile'
    }

    # Build documents list HTML
    docs_html = ""
    if verified_documents:
        for doc_type in verified_documents:
            icon = doc_icons.get(doc_type, '✅')
            name = doc_names.get(doc_type, doc_type)
            docs_html += f"""
            <div class="doc-item">
                <span class="doc-icon">{icon}</span>
                <span class="doc-name">{name}</span>
                <span class="doc-status">✅ Vérifié</span>
            </div>
            """
    else:
        docs_html = '<p class="no-docs">Aucun document vérifié</p>'

    # Expiration warning
    expiration_warning = ""
    if is_expired:
        expiration_warning = """
        <div class="alert alert-danger">
            ⚠️ Ce badge a expiré. Veuillez demander un nouveau badge au marchand.
        </div>
        """
    elif (expires_at - datetime.utcnow()).days < 30:
        days_left = (expires_at - datetime.utcnow()).days
        expiration_warning = f"""
        <div class="alert alert-warning">
            ⏰ Ce badge expire dans {days_left} jours
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vérification SmartKYC - {business_name}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }}

            .container {{
                max-width: 600px;
                width: 100%;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }}

            .header {{
                background: #1a1a2e;
                padding: 30px 20px;
                text-align: center;
            }}

            .logo {{
                height: 60px;
                margin-bottom: 15px;
            }}

            .header-title {{
                color: white;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 2px;
                opacity: 0.8;
            }}

            .content {{
                padding: 30px 20px;
            }}

            .merchant-name {{
                text-align: center;
                font-size: 28px;
                font-weight: bold;
                color: #1a1a2e;
                margin-bottom: 25px;
            }}

            .score-card {{
                background: {colors['bg']};
                border: 3px solid {colors['border']};
                border-radius: 15px;
                padding: 30px;
                text-align: center;
                margin-bottom: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }}

            .badge-label {{
                font-size: 16px;
                font-weight: bold;
                color: {colors['text']};
                opacity: 0.8;
                margin-bottom: 10px;
            }}

            .trustscore {{
                font-size: 64px;
                font-weight: bold;
                color: {colors['text']};
                line-height: 1;
                margin-bottom: 5px;
            }}

            .trustscore-max {{
                font-size: 24px;
                color: {colors['text']};
                opacity: 0.7;
            }}

            .credit-recommendation {{
                background: #f8f9fa;
                border-left: 4px solid #28a745;
                padding: 15px;
                margin-bottom: 25px;
                border-radius: 5px;
                font-size: 16px;
                color: #333;
            }}

            .section-title {{
                font-size: 18px;
                font-weight: bold;
                color: #1a1a2e;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}

            .documents-list {{
                background: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 25px;
            }}

            .doc-item {{
                display: flex;
                align-items: center;
                padding: 12px;
                background: white;
                border-radius: 8px;
                margin-bottom: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }}

            .doc-item:last-child {{
                margin-bottom: 0;
            }}

            .doc-icon {{
                font-size: 24px;
                margin-right: 12px;
            }}

            .doc-name {{
                flex: 1;
                font-size: 14px;
                color: #333;
            }}

            .doc-status {{
                font-size: 12px;
                color: #28a745;
                font-weight: bold;
            }}

            .no-docs {{
                text-align: center;
                color: #999;
                padding: 20px;
            }}

            .meta-info {{
                background: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 25px;
                font-size: 13px;
                color: #666;
            }}

            .meta-row {{
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #e0e0e0;
            }}

            .meta-row:last-child {{
                border-bottom: none;
            }}

            .meta-label {{
                font-weight: bold;
            }}

            .footer {{
                background: #1a1a2e;
                padding: 20px;
                text-align: center;
            }}

            .footer-text {{
                color: white;
                font-size: 14px;
                margin-bottom: 5px;
            }}

            .footer-link {{
                color: #FFD700;
                text-decoration: none;
                font-size: 12px;
            }}

            .alert {{
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                font-size: 14px;
            }}

            .alert-warning {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                color: #856404;
            }}

            .alert-danger {{
                background: #f8d7da;
                border-left: 4px solid #dc3545;
                color: #721c24;
            }}

            @media (max-width: 480px) {{
                .merchant-name {{
                    font-size: 22px;
                }}

                .trustscore {{
                    font-size: 48px;
                }}

                .content {{
                    padding: 20px 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="/static/logo.png" alt="SmartKYC Logo" class="logo">
                <div class="header-title">Vérification du Badge</div>
            </div>

            <div class="content">
                {expiration_warning}

                <h1 class="merchant-name">{business_name}</h1>

                <div class="score-card">
                    <div class="badge-label">🏆 BADGE {badge_level}</div>
                    <div class="trustscore">{trustscore}</div>
                    <div class="trustscore-max">/1000</div>
                </div>

                <div class="credit-recommendation">
                    {credit_rec}
                </div>

                <h2 class="section-title">
                    <span>📄</span>
                    Documents Vérifiés
                </h2>
                <div class="documents-list">
                    {docs_html}
                </div>

                <div class="meta-info">
                    <div class="meta-row">
                        <span class="meta-label">Date d'émission:</span>
                        <span>{issued_at.strftime('%d/%m/%Y')}</span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">Date d'expiration:</span>
                        <span>{expires_at.strftime('%d/%m/%Y')}</span>
                    </div>
                    <div class="meta-row">
                        <span class="meta-label">Statut:</span>
                        <span>{'❌ Expiré' if is_expired else '✅ Actif'}</span>
                    </div>
                </div>
            </div>

            <div class="footer">
                <div class="footer-text">✨ Vérifié par SmartKYC</div>
                <a href="https://smartkyc.cm" class="footer-link">smartkyc.cm</a>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def generate_404_html(verification_code: str) -> str:
    """Generate 404 HTML page for invalid verification codes."""

    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Badge Non Trouvé - SmartKYC</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }

            .container {
                max-width: 500px;
                width: 100%;
                background: white;
                border-radius: 20px;
                padding: 40px;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }

            .logo {
                height: 60px;
                margin-bottom: 20px;
            }

            .error-icon {
                font-size: 80px;
                margin-bottom: 20px;
            }

            .error-title {
                font-size: 28px;
                color: #dc3545;
                margin-bottom: 15px;
                font-weight: bold;
            }

            .error-message {
                font-size: 16px;
                color: #666;
                margin-bottom: 10px;
                line-height: 1.6;
            }

            .error-code {
                font-family: monospace;
                background: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
                color: #999;
                margin-top: 20px;
                word-break: break-all;
            }

            .footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
            }

            .footer-text {
                font-size: 14px;
                color: #999;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <img src="/static/logo.png" alt="SmartKYC Logo" class="logo">
            <div class="error-icon">❌</div>
            <h1 class="error-title">Badge Non Trouvé</h1>
            <p class="error-message">
                Le code de vérification que vous avez scanné n'existe pas ou a été révoqué.
            </p>
            <p class="error-message">
                Veuillez vérifier le QR code ou contacter le marchand pour obtenir un badge valide.
            </p>
            <div class="error-code">
                Code: """ + verification_code + """
            </div>
            <div class="footer">
                <div class="footer-text">SmartKYC - Badge de Confiance B2B</div>
            </div>
        </div>
    </body>
    </html>
    """

    return html


@router.get("/{verification_code}", response_class=HTMLResponse)
def verify_badge(verification_code: str, db: Session = Depends(get_db)):
    """
    Public verification page for badges.

    This endpoint is accessed when someone scans a QR code.
    No authentication required - this is a public page.

    Args:
        verification_code: Unique verification code from QR code
        db: Database session

    Returns:
        HTML page with merchant information and TrustScore
    """

    # Find badge by verification code
    badge = db.query(Badge).filter(
        Badge.verification_code == verification_code
    ).first()

    if not badge:
        # Return 404 HTML page
        return HTMLResponse(
            content=generate_404_html(verification_code),
            status_code=404
        )

    # Get merchant information
    merchant = db.query(Merchant).filter(
        Merchant.id == badge.merchant_id
    ).first()

    if not merchant:
        return HTMLResponse(
            content=generate_404_html(verification_code),
            status_code=404
        )

    # Get latest TrustScore
    latest_trustscore = db.query(TrustScore).filter(
        TrustScore.merchant_id == merchant.id
    ).order_by(TrustScore.created_at.desc()).first()

    trustscore_value = latest_trustscore.trustscore if latest_trustscore else 0

    # Get verified documents
    verified_docs = db.query(Document).filter(
        Document.merchant_id == merchant.id,
        Document.verification_status == VerificationStatus.VERIFIED
    ).all()

    verified_doc_types = [doc.document_type.value for doc in verified_docs]

    # Check if badge is expired
    is_expired = badge.expires_at < datetime.utcnow() or not badge.is_active

    # Generate and return HTML
    html_content = generate_verification_html(
        merchant_name=merchant.email,
        business_name=merchant.business_name or merchant.email,
        trustscore=trustscore_value,
        badge_level=badge.badge_level.value,
        verified_documents=verified_doc_types,
        issued_at=badge.issued_at,
        expires_at=badge.expires_at,
        is_expired=is_expired
    )

    return HTMLResponse(content=html_content)
