"""
SmartKYC - TrustScore Calculator
Calculates merchant TrustScore using COLD_START or NORMAL mode.
"""

import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

from sqlalchemy.orm import Session

from app.services.genuka_client import GenukaClient
from app.services.genuka_mock import GenukaAPIClientMock
from app.models import Document, VerificationStatus


# ============================================
# TRUSTSCORE THRESHOLDS
# ============================================
BADGE_THRESHOLDS = {
    'PLATINUM': 850,
    'GOLD': 700,
    'SILVER': 550,
    'BRONZE': 400,
    'NONE': 0,
}

# Cold start mode: Max score is 500 (Bronze max)
COLD_START_MAX_SCORE = 500

# Minimum months for NORMAL mode
MIN_MONTHS_FOR_NORMAL = 3


# ============================================
# TRUSTSCORE CALCULATOR
# ============================================
class TrustScoreCalculator:
    """
    Calculate TrustScore for merchants using two modes:

    - COLD_START: For merchants with < 3 months history (documents only)
    - NORMAL: For merchants with 3+ months history (full algorithm)

    Algorithm weights (NORMAL mode):
    - Documents: 10%
    - Historique: 40% (croissance, régularité, ancienneté)
    - Comportement: 30% (fidélisation, diversification, panier moyen)
    - Financiers: 20% (CA mensuel, marge brute, rotation stock)
    """

    def __init__(self, merchant_id: str, db_session: Session):
        """
        Initialize TrustScore calculator.

        Args:
            merchant_id: Unique merchant identifier
            db_session: Database session (required for document verification)
        """
        self.merchant_id = merchant_id
        self.db_session = db_session

        # Initialize Genuka API client
        self.genuka_client = GenukaClient()
        
        # Fallback mock client (only used if explicitly requested or for testing)
        self.mock_client = GenukaAPIClientMock(merchant_id)

    def calculate_trustscore(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate TrustScore for the merchant.

        Args:
            access_token: Genuka API access token (required for NORMAL mode)

        Returns:
            Dictionary containing TrustScore details
        """
        orders = []
        customers = []
        products = []

        # Fetch data from Genuka if token is provided
        if access_token:
            try:
                orders = self.genuka_client.get_orders(access_token, months=12)
                customers = self.genuka_client.get_customers(access_token)
                # products = self.genuka_client.get_products(access_token) # Not implemented in client yet
            except Exception as e:
                print(f"⚠️ Error fetching Genuka data: {e}")
                # Fallback to empty lists, will likely trigger COLD_START
                orders = []
        
        # Determine calculation mode based on data history
        calculation_mode = self._determine_calculation_mode(orders)

        if calculation_mode == "COLD_START":
            return self._calculate_cold_start()
        else:
            return self._calculate_normal(orders, customers, products)

    def _determine_calculation_mode(self, orders: List[Dict]) -> str:
        """
        Determine if we should use COLD_START or NORMAL mode.
        """
        if not orders:
            return "COLD_START"

        # Calculate number of months with orders
        completed_orders = [o for o in orders if o.get('status') == 'COMPLETED']

        if not completed_orders:
            return "COLD_START"

        # Get unique months with orders
        months_with_orders = set()
        for order in completed_orders:
            # Handle date format variations if necessary
            date_str = order.get('order_date') or order.get('created_at')
            if date_str:
                month_key = date_str[:7]  # YYYY-MM
                months_with_orders.add(month_key)

        num_months = len(months_with_orders)

        # Use COLD_START if less than 3 months of history
        return "COLD_START" if num_months < MIN_MONTHS_FOR_NORMAL else "NORMAL"

    # ========================================
    # COLD_START MODE
    # ========================================

    def _calculate_cold_start(self) -> Dict[str, Any]:
        """
        Calculate TrustScore in COLD_START mode (documents only).
        """
        # Get verified documents from DB
        verified_docs = self._get_verified_documents()

        # Calculate document score
        doc_score = 0
        doc_details = {}

        # RCCM (200 + bonuses)
        if 'RCCM' in verified_docs:
            base = 200
            # For now, assume bonuses are met if document is verified
            # In future, extract metadata from document.extracted_data
            bonus_recent = 20 
            bonus_active = 30
            rccm_score = base + bonus_recent + bonus_active
            doc_score += rccm_score
            doc_details['RCCM'] = {
                'verified': True,
                'score': rccm_score,
                'bonuses': {'recent': bonus_recent, 'active': bonus_active}
            }
        else:
            doc_details['RCCM'] = {'verified': False, 'score': 0}

        # CNI (150 + bonuses)
        if 'CNI' in verified_docs:
            base = 150
            bonus_valid = 20
            cni_score = base + bonus_valid
            doc_score += cni_score
            doc_details['CNI'] = {
                'verified': True,
                'score': cni_score,
                'bonuses': {'valid': bonus_valid}
            }
        else:
            doc_details['CNI'] = {'verified': False, 'score': 0}

        # NIF (150 + bonuses)
        if 'NIF' in verified_docs:
            base = 150
            bonus_up_to_date = 30
            nif_score = base + bonus_up_to_date
            doc_score += nif_score
            doc_details['NIF'] = {
                'verified': True,
                'score': nif_score,
                'bonuses': {'up_to_date': bonus_up_to_date}
            }
        else:
            doc_details['NIF'] = {'verified': False, 'score': 0}

        # Bank Statement (25)
        if 'BANK_STATEMENT' in verified_docs:
            doc_score += 25
            doc_details['BANK_STATEMENT'] = {'verified': True, 'score': 25}
        else:
            doc_details['BANK_STATEMENT'] = {'verified': False, 'score': 0}

        # Address Proof (25)
        if 'ADDRESS_PROOF' in verified_docs:
            doc_score += 25
            doc_details['ADDRESS_PROOF'] = {'verified': True, 'score': 25}
        else:
            doc_details['ADDRESS_PROOF'] = {'verified': False, 'score': 0}

        # Normalize to 500 max (doc_score max is 650)
        trustscore = int((doc_score / 650) * COLD_START_MAX_SCORE)

        # Determine badge
        badge = self._determine_badge(
            trustscore=trustscore,
            verified_docs=verified_docs,
            mode="COLD_START"
        )

        # Calculate validity period (6 months)
        valid_until = (datetime.now() + timedelta(days=180)).isoformat()

        return {
            "trustscore": trustscore,
            "badge": badge,
            "calculation_mode": "COLD_START",
            "metrics": {
                "documents": {
                    "score": 100,  # Always 100 in COLD_START (only component)
                    "weight": 1.0,
                    "details": doc_details,
                    "total_verified": len(verified_docs),
                },
                "historique": {
                    "score": 0,
                    "weight": 0,
                    "reason": "Insufficient history (< 3 months)"
                },
                "comportement": {
                    "score": 0,
                    "weight": 0,
                    "reason": "Insufficient history (< 3 months)"
                },
                "financiers": {
                    "score": 0,
                    "weight": 0,
                    "reason": "Insufficient history (< 3 months)"
                }
            },
            "valid_until": valid_until,
            "created_at": datetime.now().isoformat()
        }

    # ========================================
    # NORMAL MODE
    # ========================================

    def _calculate_normal(
        self,
        orders: List[Dict],
        customers: List[Dict],
        products: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate TrustScore in NORMAL mode (full algorithm).
        """
        # Get verified documents
        verified_docs = self._get_verified_documents()

        # Calculate each component (0-100 score)
        documents_metrics = self._calculate_documents_score(verified_docs)
        historique_metrics = self._calculate_historique_score(orders)
        comportement_metrics = self._calculate_comportement_score(orders, customers)
        financiers_metrics = self._calculate_financiers_score(orders, products)

        # Apply weights and calculate final score
        trustscore = (
            documents_metrics['score'] * 0.10 +
            historique_metrics['score'] * 0.40 +
            comportement_metrics['score'] * 0.30 +
            financiers_metrics['score'] * 0.20
        ) * 10  # Scale to 0-1000

        trustscore = int(trustscore)

        # Determine badge
        badge = self._determine_badge(
            trustscore=trustscore,
            verified_docs=verified_docs,
            mode="NORMAL"
        )

        # Calculate validity period (6 months)
        valid_until = (datetime.now() + timedelta(days=180)).isoformat()

        return {
            "trustscore": trustscore,
            "badge": badge,
            "calculation_mode": "NORMAL",
            "metrics": {
                "documents": documents_metrics,
                "historique": historique_metrics,
                "comportement": comportement_metrics,
                "financiers": financiers_metrics
            },
            "valid_until": valid_until,
            "created_at": datetime.now().isoformat()
        }

    # ========================================
    # COMPONENT CALCULATIONS
    # ========================================

    def _calculate_documents_score(self, verified_docs: Dict) -> Dict[str, Any]:
        """
        Calculate documents component (10% weight).
        """
        # Total possible documents: 5 (RCCM, CNI, NIF, BANK_STATEMENT, ADDRESS_PROOF)
        total_docs = 5
        verified_count = len(verified_docs)

        score = (verified_count / total_docs) * 100

        return {
            "score": score,
            "weight": 0.10,
            "verified_count": verified_count,
            "total_count": total_docs,
            "verified_types": list(verified_docs.keys()),
            "missing_types": [
                doc_type for doc_type in ['RCCM', 'CNI', 'NIF', 'BANK_STATEMENT', 'ADDRESS_PROOF']
                if doc_type not in verified_docs
            ]
        }

    def _calculate_historique_score(self, orders: List[Dict]) -> Dict[str, Any]:
        """
        Calculate historique component (40% weight).
        """
        completed_orders = [o for o in orders if o.get('status') == 'COMPLETED']

        # Calculate monthly revenues
        monthly_revenues = self._calculate_monthly_revenues(completed_orders)

        # 1. Ancienneté (number of months with orders)
        num_months = len(monthly_revenues)
        if num_months >= 24:
            anciennete_score = 100
        elif num_months >= 12:
            anciennete_score = 80
        elif num_months >= 6:
            anciennete_score = 60
        else:
            anciennete_score = 40

        # 2. Régularité (Coefficient of Variation)
        if len(monthly_revenues) > 1:
            revenues = list(monthly_revenues.values())
            mean_revenue = statistics.mean(revenues)
            std_revenue = statistics.stdev(revenues)
            cv = std_revenue / mean_revenue if mean_revenue > 0 else 1

            # CV < 20% is excellent, > 50% is poor
            if cv < 0.15:
                regularite_score = 100
            elif cv < 0.20:
                regularite_score = 90
            elif cv < 0.30:
                regularite_score = 70
            elif cv < 0.50:
                regularite_score = 50
            else:
                regularite_score = 30
        else:
            cv = 0
            regularite_score = 50

        # 3. Croissance (monthly growth rate)
        growth_rate = self._calculate_growth_rate(monthly_revenues)

        if growth_rate >= 0.05:  # 5%+ monthly growth
            croissance_score = 100
        elif growth_rate >= 0.03:  # 3%+ monthly growth
            croissance_score = 85
        elif growth_rate >= 0:  # Positive growth
            croissance_score = 70
        elif growth_rate >= -0.02:  # Slight decline
            croissance_score = 50
        else:  # Negative growth
            croissance_score = 30

        # Weighted average
        historique_score = (
            anciennete_score * 0.25 +
            regularite_score * 0.50 +
            croissance_score * 0.25
        )

        return {
            "score": historique_score,
            "weight": 0.40,
            "anciennete": {
                "score": anciennete_score,
                "months": num_months
            },
            "regularite": {
                "score": regularite_score,
                "cv": round(cv, 3)
            },
            "croissance": {
                "score": croissance_score,
                "monthly_growth_rate": round(growth_rate, 3)
            }
        }

    def _calculate_comportement_score(
        self,
        orders: List[Dict],
        customers: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate comportement component (30% weight).
        """
        completed_orders = [o for o in orders if o.get('status') == 'COMPLETED']

        # 1. Diversification (top customer concentration)
        customer_revenues = defaultdict(int)
        total_revenue = 0

        for order in completed_orders:
            cust_id = order.get('customer_id')
            total = order.get('total', 0)
            if cust_id:
                customer_revenues[cust_id] += total
            total_revenue += total

        if total_revenue > 0:
            top_customer_revenue = max(customer_revenues.values()) if customer_revenues else 0
            top_customer_pct = top_customer_revenue / total_revenue

            # Top customer < 20% is excellent
            if top_customer_pct < 0.15:
                diversification_score = 100
            elif top_customer_pct < 0.20:
                diversification_score = 90
            elif top_customer_pct < 0.30:
                diversification_score = 70
            elif top_customer_pct < 0.50:
                diversification_score = 50
            else:
                diversification_score = 30
        else:
            top_customer_pct = 0
            diversification_score = 50

        # 2. Fidélisation (recurring customers percentage)
        # Assuming customer dict has 'is_recurring' or we calculate it
        # For now, let's assume Genuka API returns this flag or we approximate
        recurring_customers = [c for c in customers if c.get('orders_count', 0) > 1]
        recurring_pct = len(recurring_customers) / len(customers) if customers else 0

        # 60%+ recurring is excellent
        if recurring_pct >= 0.70:
            fidelisation_score = 100
        elif recurring_pct >= 0.60:
            fidelisation_score = 90
        elif recurring_pct >= 0.50:
            fidelisation_score = 75
        elif recurring_pct >= 0.40:
            fidelisation_score = 60
        else:
            fidelisation_score = 40

        # 3. Panier moyen (average basket evolution)
        panier_moyen_trend = self._calculate_basket_trend(completed_orders)

        # Positive trend is good
        if panier_moyen_trend >= 0.10:  # 10%+ increase
            panier_score = 100
        elif panier_moyen_trend >= 0.05:  # 5%+ increase
            panier_score = 85
        elif panier_moyen_trend >= 0:  # Stable or slight increase
            panier_score = 70
        elif panier_moyen_trend >= -0.05:  # Slight decrease
            panier_score = 55
        else:  # Significant decrease
            panier_score = 40

        # Weighted average
        comportement_score = (
            diversification_score * 0.40 +
            fidelisation_score * 0.35 +
            panier_score * 0.25
        )

        return {
            "score": comportement_score,
            "weight": 0.30,
            "diversification": {
                "score": diversification_score,
                "top_customer_pct": round(top_customer_pct, 3)
            },
            "fidelisation": {
                "score": fidelisation_score,
                "recurring_pct": round(recurring_pct, 3),
                "recurring_count": len(recurring_customers)
            },
            "panier_moyen": {
                "score": panier_score,
                "trend": round(panier_moyen_trend, 3)
            }
        }

    def _calculate_financiers_score(
        self,
        orders: List[Dict],
        products: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calculate financiers component (20% weight).
        """
        completed_orders = [o for o in orders if o.get('status') == 'COMPLETED']

        # 1. CA mensuel (average monthly revenue)
        monthly_revenues = self._calculate_monthly_revenues(completed_orders)
        avg_monthly_revenue = statistics.mean(monthly_revenues.values()) if monthly_revenues else 0

        # Thresholds in FCFA
        if avg_monthly_revenue >= 10_000_000:  # 10M+
            ca_score = 100
        elif avg_monthly_revenue >= 5_000_000:  # 5M-10M
            ca_score = 85
        elif avg_monthly_revenue >= 3_000_000:  # 3M-5M
            ca_score = 70
        elif avg_monthly_revenue >= 1_000_000:  # 1M-3M
            ca_score = 55
        else:
            ca_score = 40

        # 2. Rotation stock (times per year)
        rotation_stock = self._calculate_stock_rotation(completed_orders, products)

        if rotation_stock >= 12:  # 12×/year
            rotation_score = 100
        elif rotation_stock >= 8:  # 8-12×/year
            rotation_score = 90
        elif rotation_stock >= 6:  # 6-8×/year
            rotation_score = 75
        elif rotation_stock >= 4:  # 4-6×/year
            rotation_score = 60
        else:
            rotation_score = 40

        # 3. Marge brute (gross margin)
        marge_brute = self._calculate_gross_margin(completed_orders, products)

        if marge_brute >= 0.35:  # 35%+
            marge_score = 100
        elif marge_brute >= 0.30:  # 30-35%
            marge_score = 90
        elif marge_brute >= 0.25:  # 25-30%
            marge_score = 75
        elif marge_brute >= 0.20:  # 20-25%
            marge_score = 60
        else:
            marge_score = 40

        # Weighted average
        financiers_score = (
            ca_score * 0.50 +
            rotation_score * 0.30 +
            marge_score * 0.20
        )

        return {
            "score": financiers_score,
            "weight": 0.20,
            "ca_mensuel": {
                "score": ca_score,
                "amount": int(avg_monthly_revenue)
            },
            "rotation_stock": {
                "score": rotation_score,
                "times_per_year": round(rotation_stock, 1)
            },
            "marge_brute": {
                "score": marge_score,
                "percentage": round(marge_brute * 100, 1)
            }
        }

    # ========================================
    # HELPER METHODS
    # ========================================

    def _get_verified_documents(self) -> Dict[str, Dict]:
        """
        Get verified documents for the merchant from the database.
        """
        if not self.db_session:
            return {}

        # Query verified documents for this merchant
        documents = self.db_session.query(Document).filter(
            Document.merchant_id == self.merchant_id,
            Document.verification_status == VerificationStatus.VERIFIED
        ).all()

        verified_docs = {}
        for doc in documents:
            # Use document type as key (RCCM, CNI, etc.)
            # Handle case where SQLAlchemy returns string instead of Enum (common in SQLite)
            doc_type = doc.document_type.value if hasattr(doc.document_type, 'value') else doc.document_type
            
            verified_docs[doc_type] = {
                'verified_at': doc.verified_at.isoformat() if doc.verified_at else None,
                'status': 'VERIFIED',
                'extracted_data': doc.extracted_data # JSON string or dict
            }
            
        return verified_docs

    def _calculate_monthly_revenues(self, orders: List[Dict]) -> Dict[str, float]:
        """
        Calculate revenue by month.
        """
        monthly_revenues = defaultdict(float)

        for order in orders:
            date_str = order.get('order_date') or order.get('created_at')
            if date_str:
                month_key = date_str[:7]  # YYYY-MM
                monthly_revenues[month_key] += float(order.get('total', 0))

        return dict(monthly_revenues)

    def _calculate_growth_rate(self, monthly_revenues: Dict[str, float]) -> float:
        """
        Calculate average monthly growth rate.
        """
        if len(monthly_revenues) < 2:
            return 0

        # Sort months chronologically
        sorted_months = sorted(monthly_revenues.items())
        revenues = [rev for _, rev in sorted_months]

        # Calculate month-over-month growth rates
        growth_rates = []
        for i in range(1, len(revenues)):
            if revenues[i-1] > 0:
                growth = (revenues[i] - revenues[i-1]) / revenues[i-1]
                growth_rates.append(growth)

        return statistics.mean(growth_rates) if growth_rates else 0

    def _calculate_basket_trend(self, orders: List[Dict]) -> float:
        """
        Calculate trend in average basket size.
        """
        if len(orders) < 10:
            return 0

        # Sort orders by date
        sorted_orders = sorted(orders, key=lambda x: x.get('order_date') or x.get('created_at') or '')

        # Split into first half and second half
        mid = len(sorted_orders) // 2
        first_half = sorted_orders[:mid]
        second_half = sorted_orders[mid:]

        # Calculate average basket for each half
        avg_first = statistics.mean([float(o.get('total', 0)) for o in first_half])
        avg_second = statistics.mean([float(o.get('total', 0)) for o in second_half])

        # Calculate trend
        if avg_first > 0:
            return (avg_second - avg_first) / avg_first
        return 0

    def _calculate_stock_rotation(
        self,
        orders: List[Dict],
        products: List[Dict]
    ) -> float:
        """
        Calculate stock rotation (times per year).
        """
        if not products:
            return 0

        # Calculate total quantity sold
        total_sold = defaultdict(int)
        for order in orders:
            for item in order.get('items', []):
                prod_id = item.get('product_id')
                if prod_id:
                    total_sold[prod_id] += item.get('quantity', 0)

        # Calculate average stock and rotation
        # This is a simplified estimation as we don't have historical stock levels
        # We use current stock as a proxy for average stock
        total_rotation_sum = 0
        product_count = 0

        for product in products:
            prod_id = str(product.get('id'))
            current_stock = product.get('stock_quantity', 0)
            sold = total_sold.get(prod_id, 0)
            
            if current_stock > 0:
                rotation = sold / current_stock
                total_rotation_sum += rotation
                product_count += 1
        
        return total_rotation_sum / product_count if product_count > 0 else 0

    def _calculate_gross_margin(
        self,
        orders: List[Dict],
        products: List[Dict]
    ) -> float:
        """
        Calculate gross margin percentage.
        """
        if not orders:
            return 0
            
        total_revenue = 0
        total_cost = 0
        
        # Create cost map
        product_costs = {str(p.get('id')): float(p.get('cost_price', 0) or 0) for p in products}
        
        for order in orders:
            total_revenue += float(order.get('total', 0))
            
            for item in order.get('items', []):
                prod_id = str(item.get('product_id'))
                qty = item.get('quantity', 0)
                cost = product_costs.get(prod_id, 0)
                total_cost += (cost * qty)
                
        if total_revenue > 0:
            return (total_revenue - total_cost) / total_revenue
        return 0

    def _determine_badge(self, trustscore: int, verified_docs: Dict, mode: str) -> str:
        """
        Determine badge level based on TrustScore and verified documents.
        """
        # Count verified documents
        num_docs = len(verified_docs)
        
        if trustscore >= BADGE_THRESHOLDS['PLATINUM']:
            # Platinum requires high score + specific docs + site visit (simulated)
            if num_docs >= 3:
                return 'PLATINUM'
            return 'GOLD'
            
        elif trustscore >= BADGE_THRESHOLDS['GOLD']:
            if num_docs >= 3:
                return 'GOLD'
            return 'SILVER'
            
        elif trustscore >= BADGE_THRESHOLDS['SILVER']:
            if num_docs >= 2:
                return 'SILVER'
            return 'BRONZE'
            
        elif trustscore >= BADGE_THRESHOLDS['BRONZE']:
            if num_docs >= 1:
                return 'BRONZE'
            return 'NONE'
            
        return 'NONE'
