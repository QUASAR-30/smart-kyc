"""
Test script for Badge Generation API
Tests QR code generation, badge image generation, and API endpoints
"""

import sys
sys.path.insert(0, '/home/quasars/Documents/smartkyc-hackathon/smartkyc/backend')

import uuid
import os
from datetime import datetime
from pathlib import Path

from app.database import SessionLocal, init_db
from app.models import (
    Merchant, Badge as BadgeModel, TrustScore as TrustScoreModel,
    BadgeLevel, SubscriptionTier, CalculationMode, BadgeLevel as TrustScoreBadgeLevel
)
from app.services.qr_generator import QRCodeGenerator
from app.services.badge_generator import BadgeGenerator
from app.utils import create_access_token
import json


def print_separator(title):
    """Print section separator"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


def test_qr_code_generation():
    """Test QR code generation"""
    print_separator("TEST 1: QR Code Generation")

    try:
        generator = QRCodeGenerator()

        # Generate test QR code
        verification_code = str(uuid.uuid4())
        qr_path = generator.generate_qr_code(
            verification_code=verification_code,
            merchant_id="test-merchant-123"
        )

        print(f"\n✅ QR code generated: {qr_path}")
        print(f"   Verification code: {verification_code}")
        print(f"   URL: https://verify.smartkyc.cm/verify/{verification_code}")

        # Verify file exists
        if os.path.exists(qr_path):
            file_size = os.path.getsize(qr_path)
            print(f"   File size: {file_size} bytes")
            print("\n✅ PASSED: QR code generation successful")

            # Cleanup
            os.remove(qr_path)
            return True
        else:
            print("\n❌ FAILED: QR code file not created")
            return False

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_badge_generation():
    """Test badge image generation for all levels"""
    print_separator("TEST 2: Badge Image Generation")

    try:
        generator = BadgeGenerator()

        badge_levels = ['BRONZE', 'SILVER', 'GOLD', 'PLATINUM']
        test_scores = [450, 600, 750, 900]

        all_passed = True

        for level, score in zip(badge_levels, test_scores):
            badge_path = generator.generate_badge(
                badge_level=level,
                trustscore=score,
                business_name="Kouassi Distribution SARL",
                merchant_id="test-merchant-badges"
            )

            if os.path.exists(badge_path):
                file_size = os.path.getsize(badge_path)
                print(f"   ✅ {level}: {badge_path} ({file_size} bytes)")
                # Cleanup
                os.remove(badge_path)
            else:
                print(f"   ❌ {level}: Badge file not created")
                all_passed = False

        if all_passed:
            print("\n✅ PASSED: Badge generation successful for all levels")
            return True
        else:
            print("\n❌ FAILED: Some badges failed to generate")
            return False

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_badge_database_integration():
    """Test badge generation with database integration"""
    print_separator("TEST 3: Badge Database Integration")

    # Initialize database
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database may already exist: {e}")

    db = SessionLocal()

    try:
        # Create test merchant
        merchant = Merchant(
            id=str(uuid.uuid4()),
            email=f"badgetest_{uuid.uuid4().hex[:8]}@example.cm",
            business_name="Badge Test Business",
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

        print(f"\n✅ Created test merchant: {merchant.email}")

        # Create a TrustScore for the merchant
        trustscore = TrustScoreModel(
            id=str(uuid.uuid4()),
            merchant_id=merchant.id,
            trustscore=780,
            badge=TrustScoreBadgeLevel.GOLD,
            metrics=json.dumps({"test": "metrics"}),
            calculation_mode=CalculationMode.NORMAL,
            valid_until=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(trustscore)
        db.commit()
        db.refresh(trustscore)

        print(f"✅ Created TrustScore: {trustscore.trustscore}/1000 ({trustscore.badge.value})")

        # Generate QR code and badge
        verification_code = str(uuid.uuid4())

        qr_generator = QRCodeGenerator()
        qr_path = qr_generator.generate_qr_code(verification_code, merchant.id)

        badge_generator = BadgeGenerator()
        badge_path = badge_generator.generate_badge(
            badge_level=trustscore.badge.value,
            trustscore=trustscore.trustscore,
            business_name=merchant.business_name,
            merchant_id=merchant.id
        )

        print(f"✅ Generated QR code: {qr_path}")
        print(f"✅ Generated badge: {badge_path}")

        # Create badge record in database
        badge = BadgeModel(
            id=str(uuid.uuid4()),
            merchant_id=merchant.id,
            badge_level=BadgeLevel.GOLD,
            badge_image_path=badge_path,
            qr_code_data=f"https://verify.smartkyc.cm/verify/{verification_code}",
            qr_code_image_path=qr_path,
            verification_code=verification_code,
            issued_at=datetime.utcnow(),
            expires_at=datetime.utcnow(),
            is_active=True
        )

        db.add(badge)
        db.commit()
        db.refresh(badge)

        print(f"\n✅ Badge saved to database:")
        print(f"   ID: {badge.id}")
        print(f"   Level: {badge.badge_level.value}")
        print(f"   Verification code: {badge.verification_code}")
        print(f"   Active: {badge.is_active}")

        # Verify retrieval
        saved_badge = db.query(BadgeModel).filter(
            BadgeModel.id == badge.id
        ).first()

        assert saved_badge is not None
        assert saved_badge.merchant_id == merchant.id
        assert saved_badge.badge_level == BadgeLevel.GOLD
        assert saved_badge.verification_code == verification_code

        print(f"\n✅ Verified badge retrieval from database")

        # Cleanup
        if os.path.exists(qr_path):
            os.remove(qr_path)
        if os.path.exists(badge_path):
            os.remove(badge_path)

        db.delete(badge)
        db.delete(trustscore)
        db.delete(merchant)
        db.commit()

        print("\n✅ PASSED: Badge database integration successful")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_badge_api_workflow():
    """Test full badge generation workflow (simulating API)"""
    print_separator("TEST 4: Badge API Workflow Simulation")

    db = SessionLocal()

    try:
        # Create merchant
        merchant = Merchant(
            id=str(uuid.uuid4()),
            email=f"workflow_{uuid.uuid4().hex[:8]}@example.cm",
            business_name="Workflow Test Company",
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

        print(f"\n✅ Step 1: Merchant created: {merchant.email}")

        # Create TrustScore
        trustscore = TrustScoreModel(
            id=str(uuid.uuid4()),
            merchant_id=merchant.id,
            trustscore=850,
            badge=TrustScoreBadgeLevel.GOLD,
            metrics=json.dumps({}),
            calculation_mode=CalculationMode.NORMAL,
            valid_until=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(trustscore)
        db.commit()

        print(f"✅ Step 2: TrustScore calculated: {trustscore.trustscore}/1000")

        # Simulate POST /api/badges/generate
        print(f"\n✅ Step 3: Calling POST /api/badges/generate")

        # Check if TrustScore exists (API validation)
        latest_trustscore = db.query(TrustScoreModel)\
            .filter(TrustScoreModel.merchant_id == merchant.id)\
            .order_by(TrustScoreModel.created_at.desc())\
            .first()

        if not latest_trustscore:
            print("   ❌ No TrustScore found")
            return False

        # Generate verification code
        verification_code = str(uuid.uuid4())

        # Generate QR code and badge
        qr_generator = QRCodeGenerator()
        qr_path = qr_generator.generate_qr_code(verification_code, merchant.id)

        badge_generator = BadgeGenerator()
        badge_path = badge_generator.generate_badge(
            badge_level=latest_trustscore.badge.value,
            trustscore=latest_trustscore.trustscore,
            business_name=merchant.business_name,
            merchant_id=merchant.id
        )

        # Save to database
        badge = BadgeModel(
            id=str(uuid.uuid4()),
            merchant_id=merchant.id,
            badge_level=BadgeLevel[latest_trustscore.badge.value],
            badge_image_path=badge_path,
            qr_code_data=f"https://verify.smartkyc.cm/verify/{verification_code}",
            qr_code_image_path=qr_path,
            verification_code=verification_code,
            issued_at=datetime.utcnow(),
            expires_at=datetime.utcnow(),
            is_active=True
        )
        db.add(badge)
        db.commit()

        print(f"   Badge ID: {badge.id}")
        print(f"   Level: {badge.badge_level.value}")
        print(f"   Verification URL: https://verify.smartkyc.cm/verify/{badge.verification_code}")

        # Simulate GET /api/badges/current
        print(f"\n✅ Step 4: Calling GET /api/badges/current")
        current_badge = db.query(BadgeModel)\
            .filter(BadgeModel.merchant_id == merchant.id)\
            .filter(BadgeModel.is_active == True)\
            .order_by(BadgeModel.issued_at.desc())\
            .first()

        if current_badge:
            print(f"   Current badge: {current_badge.badge_level.value}")
        else:
            print("   ❌ No current badge found")
            return False

        # Cleanup
        if os.path.exists(qr_path):
            os.remove(qr_path)
        if os.path.exists(badge_path):
            os.remove(badge_path)

        db.delete(badge)
        db.delete(trustscore)
        db.delete(merchant)
        db.commit()

        print("\n✅ PASSED: Badge API workflow simulation successful")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_badge_colors_and_levels():
    """Test that all badge levels have correct colors"""
    print_separator("TEST 5: Badge Colors and Levels")

    try:
        generator = BadgeGenerator()

        # Check all badge levels have colors defined
        expected_levels = ['BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'NONE']

        print("\n📋 Badge color configuration:")
        all_defined = True
        for level in expected_levels:
            if level in generator.BADGE_COLORS:
                colors = generator.BADGE_COLORS[level]
                print(f"   ✅ {level}: Primary RGB{colors['primary']}")
            else:
                print(f"   ❌ {level}: NOT DEFINED")
                all_defined = False

        if all_defined:
            print("\n✅ PASSED: All badge levels have color definitions")
            return True
        else:
            print("\n❌ FAILED: Some badge levels missing color definitions")
            return False

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return False


def run_all_tests():
    """Run all badge generation tests"""
    print("\n" + "="*70)
    print(" BADGE GENERATION API - TEST SUITE")
    print("="*70)

    results = []

    try:
        results.append(("QR Code Generation", test_qr_code_generation()))
        results.append(("Badge Image Generation", test_badge_generation()))
        results.append(("Badge Database Integration", test_badge_database_integration()))
        results.append(("Badge API Workflow", test_badge_api_workflow()))
        results.append(("Badge Colors and Levels", test_badge_colors_and_levels()))

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
            print("\n🎉 All tests passed! Badge generation system is working!")
            print("\n📝 Next steps:")
            print("   1. Start FastAPI server: uvicorn app.main:app --reload")
            print("   2. Test badge generation at: http://localhost:8000/docs")
            print("   3. POST /auth/mock-login to get token")
            print("   4. POST /api/trustscores/calculate to get TrustScore")
            print("   5. POST /api/badges/generate to create badge + QR code")
            print("   6. GET /api/badges/current to view your badge")
            print("   7. GET /api/badges/share for sharing information")
        else:
            print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please review.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
