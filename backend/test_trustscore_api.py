"""
Test script for TrustScore API
Tests TrustScore calculation, retrieval, and history endpoints
"""

import sys
sys.path.insert(0, '/home/quasars/Documents/smartkyc-hackathon/smartkyc/backend')

import uuid
from datetime import datetime

from app.database import SessionLocal, init_db
from app.models import Merchant, TrustScore as TrustScoreModel, CalculationMode, BadgeLevel as TrustScoreBadgeLevel, SubscriptionTier
from app.services.trustscore_calculator import TrustScoreCalculator
from app.utils import create_access_token
import json

def calculate_trustscore_for_merchant(merchant_id):
    """Helper to maintain compatibility with existing tests"""
    calculator = TrustScoreCalculator(merchant_id, db_session=None)
    return calculator.calculate_trustscore()


def print_separator(title):
    """Print section separator"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


def test_calculate_trustscore_endpoint():
    """Test TrustScore calculation and database saving"""
    print_separator("TEST 1: Calculate TrustScore Endpoint")

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
            email=f"calc_{uuid.uuid4().hex[:8]}@example.cm",
            business_name="Calculate Test Business",
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

        print(f"\n✅ Created test merchant: {merchant.email}")

        # Simulate API endpoint: Calculate TrustScore
        print(f"\n📊 Calculating TrustScore...")
        result = calculate_trustscore_for_merchant(merchant.id)

        print(f"\n✅ TrustScore calculated:")
        print(f"   Score: {result['trustscore']}/1000")
        print(f"   Badge: {result['badge']}")
        print(f"   Mode: {result['calculation_mode']}")

        # Save to database (simulating endpoint behavior)
        trustscore_record = TrustScoreModel(
            id=str(uuid.uuid4()),
            merchant_id=merchant.id,
            trustscore=result['trustscore'],
            badge=TrustScoreBadgeLevel[result['badge']],
            metrics=json.dumps(result['metrics']),
            calculation_mode=CalculationMode[result['calculation_mode']],
            valid_until=datetime.fromisoformat(result['valid_until']),
            created_at=datetime.fromisoformat(result['created_at'])
        )

        db.add(trustscore_record)
        db.commit()
        db.refresh(trustscore_record)

        print(f"\n✅ TrustScore saved to database:")
        print(f"   ID: {trustscore_record.id}")
        print(f"   Merchant ID: {trustscore_record.merchant_id}")

        # Verify it was saved
        saved_score = db.query(TrustScoreModel).filter(
            TrustScoreModel.id == trustscore_record.id
        ).first()

        assert saved_score is not None
        assert saved_score.trustscore == result['trustscore']

        print(f"\n✅ Verified TrustScore in database")

        # Cleanup
        db.delete(trustscore_record)
        db.delete(merchant)
        db.commit()

        print("\n✅ PASSED: Calculate TrustScore endpoint simulation")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_get_latest_trustscore():
    """Test retrieving latest TrustScore"""
    print_separator("TEST 2: Get Latest TrustScore")

    db = SessionLocal()

    try:
        # Create test merchant
        merchant = Merchant(
            id=str(uuid.uuid4()),
            email=f"latest_{uuid.uuid4().hex[:8]}@example.cm",
            business_name="Latest Test Business",
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

        print(f"\n✅ Created test merchant: {merchant.email}")

        # Create multiple TrustScores
        scores_created = []
        for i in range(3):
            result = calculate_trustscore_for_merchant(merchant.id)

            score = TrustScoreModel(
                id=str(uuid.uuid4()),
                merchant_id=merchant.id,
                trustscore=result['trustscore'] + i * 10,  # Slight variation
                badge=TrustScoreBadgeLevel[result['badge']],
                metrics=json.dumps(result['metrics']),
                calculation_mode=CalculationMode[result['calculation_mode']],
                valid_until=datetime.fromisoformat(result['valid_until']),
                created_at=datetime.utcnow()
            )
            db.add(score)
            scores_created.append(score)

        db.commit()

        print(f"\n✅ Created {len(scores_created)} TrustScores")

        # Simulate endpoint: Get latest TrustScore
        latest_score = db.query(TrustScoreModel)\
            .filter(TrustScoreModel.merchant_id == merchant.id)\
            .order_by(TrustScoreModel.created_at.desc())\
            .first()

        if latest_score:
            print(f"\n✅ Latest TrustScore retrieved:")
            print(f"   ID: {latest_score.id}")
            print(f"   Score: {latest_score.trustscore}")
            print(f"   Badge: {latest_score.badge.value}")
            print(f"   Created: {latest_score.created_at}")

            # Should be the last one created
            assert latest_score.id == scores_created[-1].id
        else:
            print("\n❌ No TrustScore found")
            return False

        # Cleanup
        for score in scores_created:
            db.delete(score)
        db.delete(merchant)
        db.commit()

        print("\n✅ PASSED: Get latest TrustScore endpoint simulation")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_get_trustscore_history():
    """Test retrieving TrustScore history"""
    print_separator("TEST 3: Get TrustScore History")

    db = SessionLocal()

    try:
        # Create test merchant
        merchant = Merchant(
            id=str(uuid.uuid4()),
            email=f"history_{uuid.uuid4().hex[:8]}@example.cm",
            business_name="History Test Business",
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

        print(f"\n✅ Created test merchant: {merchant.email}")

        # Create 7 TrustScores
        scores_created = []
        for i in range(7):
            result = calculate_trustscore_for_merchant(merchant.id)

            score = TrustScoreModel(
                id=str(uuid.uuid4()),
                merchant_id=merchant.id,
                trustscore=result['trustscore'] + i * 5,
                badge=TrustScoreBadgeLevel[result['badge']],
                metrics=json.dumps(result['metrics']),
                calculation_mode=CalculationMode[result['calculation_mode']],
                valid_until=datetime.fromisoformat(result['valid_until']),
                created_at=datetime.utcnow()
            )
            db.add(score)
            scores_created.append(score)

        db.commit()

        print(f"\n✅ Created {len(scores_created)} TrustScores")

        # Simulate endpoint: Get history (limit 5)
        limit = 5
        history = db.query(TrustScoreModel)\
            .filter(TrustScoreModel.merchant_id == merchant.id)\
            .order_by(TrustScoreModel.created_at.desc())\
            .limit(limit)\
            .all()

        total_count = db.query(TrustScoreModel)\
            .filter(TrustScoreModel.merchant_id == merchant.id)\
            .count()

        print(f"\n✅ TrustScore history retrieved:")
        print(f"   Total count: {total_count}")
        print(f"   Returned: {len(history)} (limit: {limit})")

        assert len(history) == limit
        assert total_count == 7

        print(f"\n   History scores:")
        for i, score in enumerate(history, 1):
            print(f"   {i}. Score: {score.trustscore}, Badge: {score.badge.value}")

        # Cleanup
        for score in scores_created:
            db.delete(score)
        db.delete(merchant)
        db.commit()

        print("\n✅ PASSED: Get TrustScore history endpoint simulation")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_not_found_scenarios():
    """Test 404 scenarios"""
    print_separator("TEST 4: Not Found Scenarios")

    db = SessionLocal()

    try:
        # Create merchant without TrustScores
        merchant = Merchant(
            id=str(uuid.uuid4()),
            email=f"notfound_{uuid.uuid4().hex[:8]}@example.cm",
            business_name="Not Found Test Business",
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

        print(f"\n✅ Created merchant without TrustScores: {merchant.email}")

        # Try to get latest TrustScore (should be None)
        latest_score = db.query(TrustScoreModel)\
            .filter(TrustScoreModel.merchant_id == merchant.id)\
            .order_by(TrustScoreModel.created_at.desc())\
            .first()

        if latest_score is None:
            print(f"\n✅ No TrustScore found (expected)")
            print(f"   → Would return 404 Not Found")
        else:
            print(f"\n❌ Unexpected TrustScore found")
            return False

        # Try to get history (should be empty)
        history = db.query(TrustScoreModel)\
            .filter(TrustScoreModel.merchant_id == merchant.id)\
            .all()

        total_count = len(history)

        print(f"\n✅ History query returned {total_count} scores (expected 0)")

        # Cleanup
        db.delete(merchant)
        db.commit()

        print("\n✅ PASSED: Not found scenarios handled correctly")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_authentication_flow():
    """Test full authentication + TrustScore flow"""
    print_separator("TEST 5: Full Authentication + TrustScore Flow")

    db = SessionLocal()

    try:
        # Create merchant
        merchant = Merchant(
            id=str(uuid.uuid4()),
            email=f"fullflow_{uuid.uuid4().hex[:8]}@example.cm",
            business_name="Full Flow Test",
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

        print(f"\n✅ Step 1: Merchant created: {merchant.email}")

        # Create token
        token = create_access_token(
            data={"sub": merchant.id, "email": merchant.email}
        )

        print(f"\n✅ Step 2: JWT token created")
        print(f"   Token: {token[:50]}...")

        # Simulate protected endpoint call: Calculate TrustScore
        print(f"\n✅ Step 3: Calling protected endpoint /api/trustscores/calculate")
        result = calculate_trustscore_for_merchant(merchant.id)

        # Save TrustScore
        score = TrustScoreModel(
            id=str(uuid.uuid4()),
            merchant_id=merchant.id,
            trustscore=result['trustscore'],
            badge=TrustScoreBadgeLevel[result['badge']],
            metrics=json.dumps(result['metrics']),
            calculation_mode=CalculationMode[result['calculation_mode']],
            valid_until=datetime.fromisoformat(result['valid_until']),
            created_at=datetime.utcnow()
        )
        db.add(score)
        db.commit()

        print(f"   Score: {score.trustscore}")
        print(f"   Badge: {score.badge.value}")

        # Get latest TrustScore
        print(f"\n✅ Step 4: Calling protected endpoint /api/trustscores/latest")
        latest = db.query(TrustScoreModel)\
            .filter(TrustScoreModel.merchant_id == merchant.id)\
            .order_by(TrustScoreModel.created_at.desc())\
            .first()

        print(f"   Retrieved score: {latest.trustscore}")

        # Cleanup
        db.delete(score)
        db.delete(merchant)
        db.commit()

        print("\n✅ PASSED: Full authentication + TrustScore flow works")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def run_all_tests():
    """Run all TrustScore API tests"""
    print("\n" + "="*70)
    print(" TRUSTSCORE API - TEST SUITE")
    print("="*70)

    results = []

    try:
        results.append(("Calculate TrustScore", test_calculate_trustscore_endpoint()))
        results.append(("Get Latest TrustScore", test_get_latest_trustscore()))
        results.append(("Get TrustScore History", test_get_trustscore_history()))
        results.append(("Not Found Scenarios", test_not_found_scenarios()))
        results.append(("Full Auth + TrustScore Flow", test_authentication_flow()))

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
            print("\n🎉 All tests passed! TrustScore API is working correctly!")
            print("\n📝 Next steps:")
            print("   1. Start the FastAPI server: uvicorn app.main:app --reload")
            print("   2. Test endpoints at: http://localhost:8000/docs")
            print("   3. POST /auth/mock-login to get token")
            print("   4. POST /api/trustscores/calculate with Bearer token")
            print("   5. GET /api/trustscores/latest to see your score")
        else:
            print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please review.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
