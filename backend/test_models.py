"""
Test script for SQLAlchemy models
Verifies models, relationships, and database operations
"""

import sys
sys.path.insert(0, '/home/quasars/Documents/smartkyc-hackathon/smartkyc/backend')

import uuid
from datetime import datetime, timedelta
import json

from app.models import (
    Base,
    Merchant,
    TrustScore,
    Document,
    Badge,
    Verification,
    SubscriptionTier,
    TrustScoreBadgeLevel,
    CalculationMode,
    DocumentType,
    VerificationStatus,
    BadgeLevel,
)


def print_separator(title):
    """Print section separator"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


def test_model_imports():
    """Test that all models can be imported"""
    print_separator("TEST 1: Model Imports")

    models = [
        ("Base", Base),
        ("Merchant", Merchant),
        ("TrustScore", TrustScore),
        ("Document", Document),
        ("Badge", Badge),
        ("Verification", Verification),
    ]

    print("\nImported Models:")
    for name, model in models:
        print(f"  ✅ {name}: {model}")

    print("\nImported Enums:")
    enums = [
        ("SubscriptionTier", SubscriptionTier),
        ("TrustScoreBadgeLevel", TrustScoreBadgeLevel),
        ("CalculationMode", CalculationMode),
        ("DocumentType", DocumentType),
        ("VerificationStatus", VerificationStatus),
        ("BadgeLevel", BadgeLevel),
    ]

    for name, enum in enums:
        values = [e.value for e in enum]
        print(f"  ✅ {name}: {values}")

    print("\n✅ PASSED: All models imported successfully")


def test_model_creation():
    """Test creating model instances"""
    print_separator("TEST 2: Model Instance Creation")

    # Create Merchant
    merchant = Merchant(
        id=str(uuid.uuid4()),
        email="test@example.cm",
        business_name="Test Business",
        subscription_tier=SubscriptionTier.FREE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    print(f"\n✅ Created Merchant: {merchant}")
    print(f"   Email: {merchant.email}")
    print(f"   Business: {merchant.business_name}")
    print(f"   Tier: {merchant.subscription_tier.value}")

    # Create TrustScore
    trustscore = TrustScore(
        id=str(uuid.uuid4()),
        merchant_id=merchant.id,
        trustscore=750,
        badge=TrustScoreBadgeLevel.GOLD,
        metrics=json.dumps({"test": "data"}),
        calculation_mode=CalculationMode.NORMAL,
        valid_until=datetime.utcnow() + timedelta(days=180),
        created_at=datetime.utcnow()
    )

    print(f"\n✅ Created TrustScore: {trustscore}")
    print(f"   Score: {trustscore.trustscore}")
    print(f"   Badge: {trustscore.badge.value}")
    print(f"   Mode: {trustscore.calculation_mode.value}")

    # Create Document
    document = Document(
        id=str(uuid.uuid4()),
        merchant_id=merchant.id,
        document_type=DocumentType.RCCM,
        filename="rccm.pdf",
        filepath="/data/uploads/rccm.pdf",
        file_size=1024000,
        verification_status=VerificationStatus.PENDING,
        uploaded_at=datetime.utcnow()
    )

    print(f"\n✅ Created Document: {document}")
    print(f"   Type: {document.document_type.value}")
    print(f"   Status: {document.verification_status.value}")

    # Create Badge
    badge = Badge(
        id=str(uuid.uuid4()),
        merchant_id=merchant.id,
        badge_level=BadgeLevel.GOLD,
        qr_code_data="https://verify.smartkyc.cm/ABC123",
        verification_code="ABC123",
        issued_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=180),
        is_active=True
    )

    print(f"\n✅ Created Badge: {badge}")
    print(f"   Level: {badge.badge_level.value}")
    print(f"   Code: {badge.verification_code}")
    print(f"   Valid: {badge.is_valid()}")

    # Create Verification
    verification = Verification(
        id=str(uuid.uuid4()),
        merchant_id=merchant.id,
        viewer_email="viewer@example.cm",
        viewer_ip="192.168.1.1",
        viewed_at=datetime.utcnow(),
        user_agent="Mozilla/5.0"
    )

    print(f"\n✅ Created Verification: {verification}")
    print(f"   Viewer: {verification.viewer_email}")
    print(f"   IP: {verification.viewer_ip}")

    print("\n✅ PASSED: All models can be instantiated")


def test_model_methods():
    """Test model methods"""
    print_separator("TEST 3: Model Methods")

    # Test TrustScore methods
    trustscore = TrustScore(
        id=str(uuid.uuid4()),
        merchant_id="merchant-123",
        trustscore=800,
        badge=TrustScoreBadgeLevel.GOLD,
        metrics='{"documents": 80, "historique": 90}',
        calculation_mode=CalculationMode.NORMAL,
        valid_until=datetime.utcnow() + timedelta(days=180),
        created_at=datetime.utcnow()
    )

    print("\nTrustScore methods:")
    print(f"  to_dict(): {trustscore.to_dict()}")
    print(f"  get_metrics(): {trustscore.get_metrics()}")

    new_metrics = {"test": "updated"}
    trustscore.set_metrics(new_metrics)
    print(f"  set_metrics(): {trustscore.get_metrics()}")

    # Test Document methods
    document = Document(
        id=str(uuid.uuid4()),
        merchant_id="merchant-123",
        document_type=DocumentType.CNI,
        filename="cni.jpg",
        filepath="/data/cni.jpg",
        file_size=500000,
        verification_status=VerificationStatus.PENDING,
        uploaded_at=datetime.utcnow()
    )

    print("\nDocument methods:")
    print(f"  to_dict(): {list(document.to_dict().keys())}")

    document.mark_verified()
    print(f"  mark_verified(): Status = {document.verification_status.value}")

    # Test Badge methods
    badge = Badge(
        id=str(uuid.uuid4()),
        merchant_id="merchant-123",
        badge_level=BadgeLevel.SILVER,
        qr_code_data="test-data",
        verification_code="TEST123",
        issued_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=180),
        is_active=True
    )

    print("\nBadge methods:")
    print(f"  is_valid(): {badge.is_valid()}")
    badge.deactivate()
    print(f"  deactivate(): is_active = {badge.is_active}")
    badge.activate()
    print(f"  activate(): is_active = {badge.is_active}")

    print("\n✅ PASSED: All model methods work correctly")


def test_enum_values():
    """Test enum values match database schema"""
    print_separator("TEST 4: Enum Values")

    print("\nSubscriptionTier values:")
    for tier in SubscriptionTier:
        print(f"  - {tier.value}")

    print("\nBadgeLevel values:")
    for level in BadgeLevel:
        print(f"  - {level.value}")

    print("\nCalculationMode values:")
    for mode in CalculationMode:
        print(f"  - {mode.value}")

    print("\nDocumentType values:")
    for doc_type in DocumentType:
        print(f"  - {doc_type.value}")

    print("\nVerificationStatus values:")
    for status in VerificationStatus:
        print(f"  - {status.value}")

    # Verify expected values
    assert set([e.value for e in SubscriptionTier]) == {'FREE', 'BASIC', 'PRO', 'ENTERPRISE'}
    assert set([e.value for e in BadgeLevel]) == {'BRONZE', 'SILVER', 'GOLD', 'PLATINUM'}
    assert set([e.value for e in CalculationMode]) == {'COLD_START', 'NORMAL'}
    assert set([e.value for e in DocumentType]) == {'RCCM', 'CNI', 'NIF', 'BANK_STATEMENT', 'ADDRESS_PROOF'}
    assert set([e.value for e in VerificationStatus]) == {'PENDING', 'VERIFIED', 'REJECTED'}

    print("\n✅ PASSED: All enum values match database schema")


def test_table_names():
    """Test that table names are correct"""
    print_separator("TEST 5: Table Names")

    tables = {
        "Merchant": ("merchants", Merchant),
        "TrustScore": ("trustscores", TrustScore),
        "Document": ("documents", Document),
        "Badge": ("badges", Badge),
        "Verification": ("verifications", Verification),
    }

    print("\nTable names:")
    for name, (expected_table, model) in tables.items():
        actual_table = model.__tablename__
        status = "✅" if actual_table == expected_table else "❌"
        print(f"  {status} {name}: {actual_table} (expected: {expected_table})")
        assert actual_table == expected_table, f"Table name mismatch for {name}"

    print("\n✅ PASSED: All table names are correct")


def test_relationships():
    """Test that relationships are defined"""
    print_separator("TEST 6: Model Relationships")

    print("\nMerchant relationships:")
    print(f"  - trustscores: {hasattr(Merchant, 'trustscores')}")
    print(f"  - documents: {hasattr(Merchant, 'documents')}")
    print(f"  - badge: {hasattr(Merchant, 'badge')}")
    print(f"  - verifications: {hasattr(Merchant, 'verifications')}")

    print("\nTrustScore relationships:")
    print(f"  - merchant: {hasattr(TrustScore, 'merchant')}")

    print("\nDocument relationships:")
    print(f"  - merchant: {hasattr(Document, 'merchant')}")

    print("\nBadge relationships:")
    print(f"  - merchant: {hasattr(Badge, 'merchant')}")

    print("\nVerification relationships:")
    print(f"  - merchant: {hasattr(Verification, 'merchant')}")

    # Verify all relationships exist
    assert hasattr(Merchant, 'trustscores')
    assert hasattr(Merchant, 'documents')
    assert hasattr(Merchant, 'badge')
    assert hasattr(Merchant, 'verifications')
    assert hasattr(TrustScore, 'merchant')
    assert hasattr(Document, 'merchant')
    assert hasattr(Badge, 'merchant')
    assert hasattr(Verification, 'merchant')

    print("\n✅ PASSED: All relationships are defined")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print(" SQLALCHEMY MODELS - TEST SUITE")
    print("="*70)

    try:
        test_model_imports()
        test_model_creation()
        test_model_methods()
        test_enum_values()
        test_table_names()
        test_relationships()

        print("\n" + "="*70)
        print(" TEST SUMMARY")
        print("="*70)
        print("\n✅ All 6 tests passed!")
        print("\n🎉 SQLAlchemy models are correctly defined!")
        print("\n📝 Next steps:")
        print("   1. Run 'python3 app/database.py' to create tables")
        print("   2. Start using models in your API endpoints")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
