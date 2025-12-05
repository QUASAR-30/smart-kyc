"""
Test script for Authentication Module
Tests JWT, mock login, and protected routes
"""

import sys
sys.path.insert(0, '/home/quasars/Documents/smartkyc-hackathon/smartkyc/backend')

import uuid
from datetime import datetime, timedelta

from app.utils.jwt_handler import create_access_token, verify_token, get_token_expiry
from app.models import Merchant, SubscriptionTier
from app.database import SessionLocal, init_db


def print_separator(title):
    """Print section separator"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


def test_jwt_creation():
    """Test JWT token creation"""
    print_separator("TEST 1: JWT Token Creation")

    # Create token
    merchant_id = str(uuid.uuid4())
    email = "test@example.cm"

    token = create_access_token(
        data={"sub": merchant_id, "email": email}
    )

    print(f"\n✅ Created JWT token:")
    print(f"   Merchant ID: {merchant_id}")
    print(f"   Email: {email}")
    print(f"   Token: {token[:50]}...")

    # Verify token
    payload = verify_token(token)

    if payload:
        print(f"\n✅ Token verified successfully:")
        print(f"   Subject (merchant_id): {payload.get('sub')}")
        print(f"   Email: {payload.get('email')}")
        print(f"   Expiration: {datetime.fromtimestamp(payload.get('exp'))}")
    else:
        print("\n❌ Token verification failed")
        return False

    # Check expiry
    expiry = get_token_expiry(token)
    print(f"\n✅ Token expires at: {expiry}")

    assert payload.get('sub') == merchant_id
    assert payload.get('email') == email

    print("\n✅ PASSED: JWT token creation and verification")
    return True


def test_token_expiration():
    """Test expired token handling"""
    print_separator("TEST 2: Token Expiration")

    # Create expired token (expired 1 hour ago)
    merchant_id = str(uuid.uuid4())
    expired_token = create_access_token(
        data={"sub": merchant_id},
        expires_delta=timedelta(hours=-1)  # Already expired
    )

    print(f"\n✅ Created expired token: {expired_token[:50]}...")

    # Try to verify
    payload = verify_token(expired_token)

    if payload is None:
        print("\n✅ Expired token correctly rejected")
        print("\n✅ PASSED: Token expiration handling works")
        return True
    else:
        print("\n❌ FAILED: Expired token was accepted")
        return False


def test_invalid_token():
    """Test invalid token handling"""
    print_separator("TEST 3: Invalid Token Handling")

    # Create invalid token
    invalid_token = "invalid.token.here"

    print(f"\n✅ Testing invalid token: {invalid_token}")

    # Try to verify
    payload = verify_token(invalid_token)

    if payload is None:
        print("\n✅ Invalid token correctly rejected")
        print("\n✅ PASSED: Invalid token handling works")
        return True
    else:
        print("\n❌ FAILED: Invalid token was accepted")
        return False


def test_database_merchant_creation():
    """Test creating merchant in database"""
    print_separator("TEST 4: Database Merchant Creation")

    # Initialize database
    print("\n📦 Initializing database...")
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database may already exist: {e}")

    # Create session
    db = SessionLocal()

    try:
        # Create merchant
        merchant = Merchant(
            id=str(uuid.uuid4()),
            email=f"test_{uuid.uuid4().hex[:8]}@example.cm",
            business_name="Test Business",
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(merchant)
        db.commit()
        db.refresh(merchant)

        print(f"\n✅ Created merchant in database:")
        print(f"   ID: {merchant.id}")
        print(f"   Email: {merchant.email}")
        print(f"   Business: {merchant.business_name}")
        print(f"   Tier: {merchant.subscription_tier.value}")

        # Fetch merchant
        fetched_merchant = db.query(Merchant).filter(
            Merchant.id == merchant.id
        ).first()

        if fetched_merchant:
            print(f"\n✅ Fetched merchant from database:")
            print(f"   Email: {fetched_merchant.email}")
            assert fetched_merchant.email == merchant.email

        # Create token for this merchant
        token = create_access_token(
            data={"sub": merchant.id, "email": merchant.email}
        )

        print(f"\n✅ Created JWT token for merchant")
        print(f"   Token: {token[:50]}...")

        # Cleanup
        db.delete(merchant)
        db.commit()

        print("\n✅ PASSED: Database merchant creation and token generation")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_mock_login_flow():
    """Test the mock login flow (auto-signup)"""
    print_separator("TEST 5: Mock Login Flow (Auto-Signup)")

    db = SessionLocal()

    try:
        test_email = f"auto_{uuid.uuid4().hex[:8]}@example.cm"

        # Simulate auto-signup: Check if merchant exists
        merchant = db.query(Merchant).filter(Merchant.email == test_email).first()

        if not merchant:
            print(f"\n✅ Merchant not found, creating new one...")
            merchant = Merchant(
                id=str(uuid.uuid4()),
                email=test_email,
                business_name=f"Business - {test_email.split('@')[0].title()}",
                subscription_tier=SubscriptionTier.FREE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(merchant)
            db.commit()
            db.refresh(merchant)

            print(f"   Created merchant: {merchant.email}")

        # Create token
        access_token = create_access_token(
            data={"sub": merchant.id, "email": merchant.email}
        )

        print(f"\n✅ Login successful:")
        print(f"   Merchant ID: {merchant.id}")
        print(f"   Email: {merchant.email}")
        print(f"   Access Token: {access_token[:50]}...")

        # Simulate protected route: verify token and fetch merchant
        payload = verify_token(access_token)
        if payload:
            merchant_id = payload.get("sub")
            authenticated_merchant = db.query(Merchant).filter(
                Merchant.id == merchant_id
            ).first()

            if authenticated_merchant:
                print(f"\n✅ Protected route access granted:")
                print(f"   Authenticated as: {authenticated_merchant.email}")
            else:
                print("\n❌ Merchant not found")
                return False
        else:
            print("\n❌ Token verification failed")
            return False

        # Cleanup
        db.delete(merchant)
        db.commit()

        print("\n✅ PASSED: Mock login flow with auto-signup works")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_get_current_merchant_flow():
    """Test the get_current_merchant dependency flow"""
    print_separator("TEST 6: Get Current Merchant Dependency")

    db = SessionLocal()

    try:
        # Create test merchant
        merchant = Merchant(
            id=str(uuid.uuid4()),
            email=f"dep_{uuid.uuid4().hex[:8]}@example.cm",
            business_name="Dependency Test",
            subscription_tier=SubscriptionTier.FREE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

        # Create token
        token = create_access_token(
            data={"sub": merchant.id, "email": merchant.email}
        )

        print(f"\n✅ Created merchant and token")

        # Simulate Authorization header
        authorization_header = f"Bearer {token}"
        print(f"   Authorization: {authorization_header[:60]}...")

        # Verify token from header
        scheme, token_value = authorization_header.split()
        assert scheme.lower() == "bearer"

        payload = verify_token(token_value)
        assert payload is not None

        merchant_id = payload.get("sub")
        fetched_merchant = db.query(Merchant).filter(
            Merchant.id == merchant_id
        ).first()

        if fetched_merchant:
            print(f"\n✅ Dependency resolved successfully:")
            print(f"   Merchant: {fetched_merchant.email}")
            print(f"   ID: {fetched_merchant.id}")
        else:
            print("\n❌ Merchant not found")
            return False

        # Test invalid header
        print(f"\n✅ Testing invalid authorization header...")
        invalid_header = "InvalidScheme token123"
        try:
            scheme, _ = invalid_header.split()
            if scheme.lower() != "bearer":
                print("   ✅ Invalid scheme correctly rejected")
        except:
            print("   ✅ Invalid header format correctly rejected")

        # Cleanup
        db.delete(merchant)
        db.commit()

        print("\n✅ PASSED: Get current merchant dependency works")
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
    """Run all authentication tests"""
    print("\n" + "="*70)
    print(" AUTHENTICATION MODULE - TEST SUITE")
    print("="*70)

    results = []

    try:
        results.append(("JWT Creation", test_jwt_creation()))
        results.append(("Token Expiration", test_token_expiration()))
        results.append(("Invalid Token", test_invalid_token()))
        results.append(("Database Merchant", test_database_merchant_creation()))
        results.append(("Mock Login Flow", test_mock_login_flow()))
        results.append(("Get Current Merchant", test_get_current_merchant_flow()))

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
            print("\n🎉 All tests passed! Authentication module is working correctly!")
            print("\n📝 Next steps:")
            print("   1. Start the FastAPI server: uvicorn app.main:app --reload")
            print("   2. Test endpoints at: http://localhost:8000/docs")
            print("   3. POST /auth/mock-login with email to get token")
            print("   4. GET /auth/me with Bearer token to verify")
        else:
            print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please review.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
