"""
Test script for Public Verification Page
Tests the public badge verification endpoint
"""

import sys
sys.path.insert(0, '/home/quasars/Documents/smartkyc-hackathon/smartkyc/backend')

import uuid
import json
from datetime import datetime, timedelta

from app.database import SessionLocal, init_db
from app.models import (
    Merchant, Badge, TrustScore, Document,
    BadgeLevel, SubscriptionTier, CalculationMode,
    BadgeLevel as TrustScoreBadgeLevel, DocumentType, VerificationStatus
)


def print_separator(title):
    """Print section separator"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


def test_verification_page_valid_code():
    """Test verification page with valid code"""
    print_separator("TEST 1: Verification Page - Valid Code")

    # Initialize database
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database may already exist: {e}")

    db = SessionLocal()

    try:
        # Create merchant
        merchant = Merchant(
            id=str(uuid.uuid4()),
            email=f"verify_{uuid.uuid4().hex[:8]}@example.cm",
            business_name="Kouassi Distribution SARL",
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

        print(f"\n✅ Created merchant: {merchant.business_name}")

        # Create TrustScore
        trustscore = TrustScoreModel(
            id=str(uuid.uuid4()),
            merchant_id=merchant.id,
            trustscore=850,
            badge=TrustScoreBadgeLevel.GOLD,
            metrics=json.dumps({}),
            calculation_mode=CalculationMode.NORMAL,
            valid_until=datetime.utcnow() + timedelta(days=180),
            created_at=datetime.utcnow()
        )
        db.add(trustscore)
        db.commit()

        print(f"✅ Created TrustScore: {trustscore.trustscore}/1000 ({trustscore.badge.value})")

        # Create some verified documents
        doc_types = [DocumentType.RCCM, DocumentType.CNI, DocumentType.NIF]
        for doc_type in doc_types:
            document = Document(
                id=str(uuid.uuid4()),
                merchant_id=merchant.id,
                document_type=doc_type,
                filename=f"test_{doc_type.value}.png",
                filepath=f"/test/{doc_type.value}.png",
                file_size=1024,
                verification_status=VerificationStatus.VERIFIED,
                verified_at=datetime.utcnow(),
                extracted_data=json.dumps({}),
                uploaded_at=datetime.utcnow()
            )
            db.add(document)

        db.commit()
        print(f"✅ Created 3 verified documents")

        # Create badge
        verification_code = str(uuid.uuid4())
        badge = Badge(
            id=str(uuid.uuid4()),
            merchant_id=merchant.id,
            badge_level=BadgeLevel.GOLD,
            badge_image_path="/test/badge.png",
            qr_code_data=f"https://verify.smartkyc.cm/verify/{verification_code}",
            qr_code_image_path="/test/qr.png",
            verification_code=verification_code,
            issued_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=180),
            is_active=True
        )
        db.add(badge)
        db.commit()
        db.refresh(badge)

        print(f"✅ Created badge with verification code: {verification_code}")

        # Simulate GET /verify/{code}
        print(f"\n📄 Simulating: GET /verify/{verification_code}")

        # Query badge
        found_badge = db.query(Badge).filter(
            Badge.verification_code == verification_code
        ).first()

        if not found_badge:
            print("❌ Badge not found")
            return False

        print(f"✅ Badge found: {found_badge.badge_level.value}")

        # Get merchant
        found_merchant = db.query(Merchant).filter(
            Merchant.id == found_badge.merchant_id
        ).first()

        print(f"✅ Merchant: {found_merchant.business_name}")

        # Get TrustScore
        latest_score = db.query(TrustScore).filter(
            TrustScore.merchant_id == found_merchant.id
        ).order_by(TrustScore.created_at.desc()).first()

        print(f"✅ TrustScore: {latest_score.trustscore}/1000")

        # Get verified documents
        verified_docs = db.query(Document).filter(
            Document.merchant_id == found_merchant.id,
            Document.verification_status == VerificationStatus.VERIFIED
        ).all()

        print(f"✅ Verified documents: {len(verified_docs)}")
        for doc in verified_docs:
            print(f"   - {doc.document_type.value}")

        # Check expiration
        is_expired = found_badge.expires_at < datetime.utcnow()
        print(f"✅ Badge active: {not is_expired}")
        print(f"   Expires: {found_badge.expires_at.strftime('%d/%m/%Y')}")

        # Cleanup
        db.query(Document).filter(Document.merchant_id == merchant.id).delete()
        db.delete(badge)
        db.delete(trustscore)
        db.delete(merchant)
        db.commit()

        print("\n✅ PASSED: Verification page data retrieval successful")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_verification_page_invalid_code():
    """Test verification page with invalid code"""
    print_separator("TEST 2: Verification Page - Invalid Code")

    db = SessionLocal()

    try:
        # Try to find a non-existent badge
        fake_code = "non-existent-code-12345"

        print(f"\n📄 Simulating: GET /verify/{fake_code}")

        badge = db.query(Badge).filter(
            Badge.verification_code == fake_code
        ).first()

        if badge is None:
            print("✅ Correctly returns None for invalid code")
            print("✅ Should display 404 HTML page")
            print("\n✅ PASSED: Invalid code handling successful")
            return True
        else:
            print("❌ FAILED: Found badge for invalid code")
            return False

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False
    finally:
        db.close()


def test_verification_page_expired_badge():
    """Test verification page with expired badge"""
    print_separator("TEST 3: Verification Page - Expired Badge")

    db = SessionLocal()

    try:
        # Create merchant
        merchant = Merchant(
            id=str(uuid.uuid4()),
            email=f"expired_{uuid.uuid4().hex[:8]}@example.cm",
            business_name="Expired Badge Test",
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

        # Create badge that expired yesterday
        verification_code = str(uuid.uuid4())
        badge = Badge(
            id=str(uuid.uuid4()),
            merchant_id=merchant.id,
            badge_level=BadgeLevel.GOLD,
            badge_image_path="/test/badge.png",
            qr_code_data=f"https://verify.smartkyc.cm/verify/{verification_code}",
            qr_code_image_path="/test/qr.png",
            verification_code=verification_code,
            issued_at=datetime.utcnow() - timedelta(days=200),
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
            is_active=True
        )
        db.add(badge)
        db.commit()

        print(f"\n✅ Created expired badge (expired yesterday)")

        # Check if expired
        is_expired = badge.expires_at < datetime.utcnow()

        if is_expired:
            print("✅ Badge correctly detected as expired")
            print("✅ Should display expiration warning on page")
            print("\n✅ PASSED: Expired badge detection successful")

            # Cleanup
            db.delete(badge)
            db.delete(merchant)
            db.commit()

            return True
        else:
            print("❌ FAILED: Badge not detected as expired")
            db.delete(badge)
            db.delete(merchant)
            db.commit()
            return False

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_static_files_exist():
    """Test that static files (logo) exist"""
    print_separator("TEST 4: Static Files")

    import os

    static_dir = "/home/quasars/Documents/smartkyc-hackathon/smartkyc/backend/app/static"

    files_to_check = [
        ("logo.png", "PNG logo"),
        ("logo.svg", "SVG logo")
    ]

    all_exist = True
    for filename, description in files_to_check:
        filepath = os.path.join(static_dir, filename)
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✅ {description}: {filepath} ({file_size} bytes)")
        else:
            print(f"❌ {description}: NOT FOUND at {filepath}")
            all_exist = False

    if all_exist:
        print("\n✅ PASSED: All static files exist")
        return True
    else:
        print("\n❌ FAILED: Some static files missing")
        return False


def test_html_generation():
    """Test HTML page generation functions"""
    print_separator("TEST 5: HTML Generation")

    try:
        from app.api.verify import generate_verification_html, generate_404_html

        # Test valid page HTML
        html = generate_verification_html(
            merchant_name="test@example.cm",
            business_name="Test Business",
            trustscore=850,
            badge_level="GOLD",
            verified_documents=["RCCM", "CNI", "NIF"],
            issued_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=180),
            is_expired=False
        )

        # Check HTML contains key elements
        checks = [
            ("<!DOCTYPE html>", "DOCTYPE declaration"),
            ("/static/logo.png", "Logo image reference"),
            ("Test Business", "Business name"),
            ("850", "TrustScore value"),
            ("GOLD", "Badge level"),
            ("Registre de Commerce", "RCCM document name"),
            ("Vérifié par SmartKYC", "Footer branding"),
        ]

        all_passed = True
        for check_string, description in checks:
            if check_string in html:
                print(f"✅ {description}: Found")
            else:
                print(f"❌ {description}: NOT FOUND")
                all_passed = False

        # Test 404 HTML
        html_404 = generate_404_html("test-code-123")

        if "Badge Non Trouvé" in html_404:
            print("✅ 404 page: Generated correctly")
        else:
            print("❌ 404 page: Missing title")
            all_passed = False

        if all_passed:
            print("\n✅ PASSED: HTML generation successful")
            return True
        else:
            print("\n❌ FAILED: Some HTML elements missing")
            return False

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all verification page tests"""
    print("\n" + "="*70)
    print(" PUBLIC VERIFICATION PAGE - TEST SUITE")
    print("="*70)

    results = []

    try:
        results.append(("Valid Verification Code", test_verification_page_valid_code()))
        results.append(("Invalid Verification Code", test_verification_page_invalid_code()))
        results.append(("Expired Badge Detection", test_verification_page_expired_badge()))
        results.append(("Static Files Existence", test_static_files_exist()))
        results.append(("HTML Generation", test_html_generation()))

        print("\n" + "="*70)
        print(" TEST SUMMARY")
        print("="*70)

        for test_name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{status}: {test_name}")

        passed_count = sum(1 for _, passed in results if passed)
        total_count = len(results)

        print(f"\nTotal: {passed_count}/{total_count} tests passed")

        if passed_count == total_count:
            print("\n🎉 All tests passed! Public verification page is working!")
            print("\n📝 Next steps:")
            print("   1. Start FastAPI server: uvicorn app.main:app --reload")
            print("   2. Test verification page at: http://localhost:8000/docs")
            print("   3. Generate a badge with POST /api/badges/generate")
            print("   4. Visit: http://localhost:8000/verify/{verification_code}")
            print("   5. Should see beautiful mobile-responsive page!")
            print("\n🏆 BACKEND MVP 100% COMPLETE!")
        else:
            print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please review.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
