"""
Test script for TrustScoreCalculator
Verifies COLD_START and NORMAL mode calculations using mocks
"""

import sys
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, '/home/quasars/Documents/smartkyc-hackathon/smartkyc/backend')

from app.services.trustscore_calculator import TrustScoreCalculator
from app.models import Document, VerificationStatus, DocumentType

class TestTrustScoreCalculator(unittest.TestCase):

    def setUp(self):
        self.merchant_id = "test-merchant-id"
        self.mock_db = MagicMock()
        self.calculator = TrustScoreCalculator(self.merchant_id, self.mock_db)
        
        # Mock GenukaClient
        self.calculator.genuka_client = MagicMock()

    def test_cold_start_mode(self):
        """Test calculation in COLD_START mode (no orders)"""
        # Setup mocks
        self.calculator.genuka_client.get_orders.return_value = []
        
        # Mock DB documents
        mock_doc = MagicMock(spec=Document)
        mock_doc.document_type = DocumentType.RCCM
        mock_doc.verification_status = VerificationStatus.VERIFIED
        mock_doc.verified_at = datetime.now()
        mock_doc.extracted_data = {}
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_doc]

        # Execute
        result = self.calculator.calculate_trustscore(access_token="fake-token")

        # Assertions
        self.assertEqual(result['calculation_mode'], 'COLD_START')
        self.assertLessEqual(result['trustscore'], 500)
        self.assertEqual(result['metrics']['documents']['total_verified'], 1)
        self.assertTrue(result['metrics']['documents']['details']['RCCM']['verified'])

    def test_normal_mode(self):
        """Test calculation in NORMAL mode (sufficient history)"""
        # Setup mocks
        # Create 12 months of orders
        orders = []
        for i in range(12):
            date = (datetime.now() - timedelta(days=30*i)).strftime("%Y-%m-%d")
            orders.append({
                'id': f'order-{i}',
                'status': 'COMPLETED',
                'total': 100000,
                'created_at': date
            })
        
        self.calculator.genuka_client.get_orders.return_value = orders
        self.calculator.genuka_client.get_customers.return_value = [{'id': 'c1', 'orders_count': 5}]
        
        # Mock DB documents
        self.mock_db.query.return_value.filter.return_value.all.return_value = []

        # Execute
        result = self.calculator.calculate_trustscore(access_token="fake-token")

        # Assertions
        self.assertEqual(result['calculation_mode'], 'NORMAL')
        self.assertGreater(result['trustscore'], 0)
        self.assertEqual(result['metrics']['historique']['anciennete']['months'], 12)

    def test_badge_determination(self):
        """Test badge logic"""
        # Test Platinum
        badge = self.calculator._determine_badge(900, {'RCCM': {}, 'CNI': {}, 'NIF': {}}, 'NORMAL')
        self.assertEqual(badge, 'PLATINUM')
        
        # Test Gold (High score but missing docs)
        badge = self.calculator._determine_badge(900, {'RCCM': {}}, 'NORMAL')
        self.assertEqual(badge, 'GOLD')
        
        # Test Bronze
        badge = self.calculator._determine_badge(450, {'RCCM': {}}, 'NORMAL')
        self.assertEqual(badge, 'BRONZE')

if __name__ == '__main__':
    unittest.main()
