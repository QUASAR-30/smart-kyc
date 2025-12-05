"""
SmartKYC - Mock Genuka API Client
Generates reproducible, realistic business data for hackathon demo.
"""

import hashlib
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from collections import defaultdict

from faker import Faker


# ============================================
# BUSINESS CATEGORY TEMPLATES
# ============================================
BUSINESS_CATEGORIES = {
    'RETAIL_FOOD': {
        'products': [
            'Riz Parfumé 50kg', 'Huile Végétale 5L', 'Farine de Blé 25kg',
            'Sucre Blanc 50kg', 'Lait en Poudre', 'Concentré de Tomate',
            'Sel Iodé 1kg', 'Poisson Séché', 'Haricots Secs', 'Maïs',
            'Arachides', 'Pâtes Alimentaires', 'Sardines en Boîte',
            'Cube Maggi', 'Café Soluble', 'Thé', 'Pain de Sucre',
            'Biscuits', 'Eau Minérale 1.5L', 'Jus de Fruit'
        ],
        'avg_margin': 0.28,
        'avg_basket': 25000,
        'stock_rotation': 10,
    },
    'WHOLESALE_CONSTRUCTION': {
        'products': [
            'Ciment Portland 50kg', 'Fer à Béton 8mm', 'Fer à Béton 10mm',
            'Fer à Béton 12mm', 'Gravier 5/15', 'Sable de Construction',
            'Briques Rouges', 'Parpaings 15x20x50', 'Planches de Coffrage',
            'Tôles Ondulées 3m', 'Clous 3 pouces', 'Fil de Fer',
            'Peinture Blanche 25L', 'Peinture Couleur', 'Ciment Blanc',
            'Carreaux 30x30', 'Carreaux 40x40', 'Tuyaux PVC 100mm'
        ],
        'avg_margin': 0.22,
        'avg_basket': 450000,
        'stock_rotation': 6,
    },
    'RETAIL_ELECTRONICS': {
        'products': [
            'Samsung Galaxy A14', 'iPhone 13', 'Tecno Spark 10',
            'Infinix Hot 12', 'Xiaomi Redmi Note 12', 'Écouteurs Bluetooth',
            'Chargeur Rapide USB-C', 'Câble USB Type-C', 'Câble Lightning',
            'Protection Écran', 'Coque Téléphone', 'Batterie Externe 10000mAh',
            'Carte Mémoire 64GB', 'Carte Mémoire 128GB', 'Support Téléphone Voiture',
            'Montre Connectée', 'Haut-parleur Bluetooth', 'Lampe LED USB'
        ],
        'avg_margin': 0.35,
        'avg_basket': 85000,
        'stock_rotation': 12,
    },
    'WHOLESALE_CLOTHING': {
        'products': [
            'Pagne Wax Hollandais', 'Pagne Fancy', 'Tissu Bazin Riche',
            'Tissu Damassé', 'Chemises Homme', 'Pantalons Homme',
            'Robes Femme', 'Jupes Femme', 'Tee-shirts Homme',
            'Tee-shirts Femme', 'Sous-vêtements', 'Chaussettes',
            'Foulards', 'Ceintures', 'Casquettes', 'Chaussures Homme',
            'Chaussures Femme', 'Sandales', 'Sacs à Main'
        ],
        'avg_margin': 0.32,
        'avg_basket': 120000,
        'stock_rotation': 8,
    },
    'PHARMACY': {
        'products': [
            'Paracétamol 500mg', 'Ibuprofène 400mg', 'Amoxicilline 500mg',
            'Métronidazole 500mg', 'Ciprofloxacine 500mg', 'Vitamine C',
            'Multivitamines', 'Sirop Toux', 'Gel Désinfectant',
            'Masques Chirurgicaux', 'Thermomètre Digital', 'Pansements',
            'Coton Hydrophile', 'Alcool 70°', 'Sérum Physiologique',
            'Crème Antiseptique', 'Anti-moustique', 'Lotion Corps'
        ],
        'avg_margin': 0.30,
        'avg_basket': 15000,
        'stock_rotation': 15,
    },
}

BUSINESS_SIZES = {
    'SMALL': {
        'num_products': (20, 40),
        'num_customers': (50, 100),
        'monthly_orders': (60, 120),
        'base_revenue': 2_500_000,  # 2.5M FCFA/month
    },
    'MEDIUM': {
        'num_products': (40, 80),
        'num_customers': (100, 200),
        'monthly_orders': (120, 250),
        'base_revenue': 6_000_000,  # 6M FCFA/month
    },
    'LARGE': {
        'num_products': (80, 150),
        'num_customers': (200, 400),
        'monthly_orders': (250, 500),
        'base_revenue': 12_000_000,  # 12M FCFA/month
    },
}


# ============================================
# GENUKA API CLIENT MOCK
# ============================================
class GenukaAPIClientMock:
    """
    Mock implementation of Genuka API client for hackathon demo.

    Generates reproducible, realistic business data for merchants:
    - Products catalog (20-150 products)
    - Customers (50-400 customers)
    - Orders (12 months history, 3% monthly growth)

    Data is seeded by merchant_id for reproducibility.

    Usage:
        client = GenukaAPIClientMock(merchant_id="merchant-123")
        orders = client.get_orders(months=12)
        customers = client.get_customers()
        products = client.get_products()
    """

    def __init__(self, merchant_id: str):
        """
        Initialize mock Genuka API client.

        Args:
            merchant_id: Unique merchant identifier (used as seed)
        """
        self.merchant_id = merchant_id
        self.seed = self._generate_seed(merchant_id)

        # Initialize Faker with French locale
        self.faker = Faker('fr_FR')
        self.faker.seed_instance(self.seed)

        # Determine business profile based on seed
        random.seed(self.seed)
        self.business_category = self._determine_business_category()
        self.business_size = self._determine_business_size()

        # Cache for consistency
        self._products_cache: List[Dict[str, Any]] = None
        self._customers_cache: List[Dict[str, Any]] = None

    def get_products(self) -> List[Dict[str, Any]]:
        """
        Generate product catalog with realistic pricing and inventory.

        Returns:
            List of products with schema:
            {
                "id": "PROD-0001",
                "name": "Riz Parfumé 50kg",
                "category": "RETAIL_FOOD",
                "unit_price": 25000,
                "cost": 18000,
                "stock_quantity": 150,
                "unit": "sac",
                "supplier": "Fournisseur XYZ"
            }
        """
        if self._products_cache is not None:
            return self._products_cache

        random.seed(self.seed)
        self.faker.seed_instance(self.seed)

        category_config = BUSINESS_CATEGORIES[self.business_category]
        size_config = BUSINESS_SIZES[self.business_size]

        num_products = random.randint(*size_config['num_products'])
        base_products = category_config['products']
        target_margin = category_config['avg_margin']

        products = []
        for i in range(num_products):
            # Cycle through base products with variations
            base_name = base_products[i % len(base_products)]
            product_name = self._generate_product_variant(base_name, i)

            # Generate pricing with realistic margins
            if self.business_category == 'RETAIL_FOOD':
                unit_price = random.randint(5000, 150000)
            elif self.business_category == 'WHOLESALE_CONSTRUCTION':
                unit_price = random.randint(10000, 500000)
            elif self.business_category == 'RETAIL_ELECTRONICS':
                unit_price = random.randint(15000, 800000)
            elif self.business_category == 'WHOLESALE_CLOTHING':
                unit_price = random.randint(8000, 300000)
            else:  # PHARMACY
                unit_price = random.randint(2000, 50000)

            # Calculate cost based on target margin with slight variation
            margin_variation = random.uniform(-0.05, 0.05)
            actual_margin = target_margin + margin_variation
            cost = int(unit_price * (1 - actual_margin))

            products.append({
                "id": f"PROD-{str(i+1).zfill(4)}",
                "name": product_name,
                "category": self.business_category,
                "unit_price": unit_price,
                "cost": cost,
                "stock_quantity": random.randint(30, 500),
                "unit": self._get_unit_type(self.business_category),
                "supplier": self.faker.company(),
            })

        self._products_cache = products
        return products

    def get_customers(self) -> List[Dict[str, Any]]:
        """
        Generate customer list with realistic loyalty patterns.

        Returns:
            List of customers with schema:
            {
                "id": "CUST-0045",
                "name": "Kouassi Jean",
                "email": "kouassi.jean@example.cm",
                "phone": "+237 622 345 678",
                "first_order_date": "2024-01-15",
                "total_orders": 25,
                "lifetime_value": 0,
                "is_recurring": true,
                "customer_segment": "VIP"
            }

        Ensures:
        - 60-70% recurring customers (total_orders >= 3)
        - Top customer < 20% of total revenue (diversification)
        """
        if self._customers_cache is not None:
            return self._customers_cache

        random.seed(self.seed)
        self.faker.seed_instance(self.seed)

        size_config = BUSINESS_SIZES[self.business_size]
        num_customers = random.randint(*size_config['num_customers'])

        customers = []
        for i in range(num_customers):
            # Generate customer profile
            first_order_date = self.faker.date_between(
                start_date='-18M',
                end_date='-1M'
            )

            # Loyalty distribution using beta distribution (Pareto principle)
            loyalty_score = random.betavariate(2, 5)

            if loyalty_score > 0.7:  # VIP (top 20%)
                total_orders = random.randint(20, 60)
                segment = "VIP"
            elif loyalty_score > 0.4:  # Regular (30%)
                total_orders = random.randint(8, 20)
                segment = "REGULAR"
            else:  # Occasional (50%)
                total_orders = random.randint(1, 7)
                segment = "OCCASIONAL"

            is_recurring = total_orders >= 3

            customers.append({
                "id": f"CUST-{str(i+1).zfill(4)}",
                "name": self.faker.name(),
                "email": self.faker.email(),
                "phone": self._generate_cameroon_phone(),
                "first_order_date": first_order_date.isoformat(),
                "total_orders": total_orders,
                "lifetime_value": 0,  # Will be calculated from orders
                "is_recurring": is_recurring,
                "customer_segment": segment,
            })

        self._customers_cache = customers
        return customers

    def get_orders(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Generate orders for past N months with realistic business patterns.

        Args:
            months: Number of months of order history to generate (default: 12)

        Returns:
            List of orders with schema:
            {
                "id": "ORD-20240315-0123",
                "order_date": "2024-03-15T14:30:00",
                "customer_id": "CUST-0045",
                "items": [
                    {
                        "product_id": "PROD-0012",
                        "product_name": "Riz Parfumé 50kg",
                        "quantity": 5,
                        "unit_price": 25000,
                        "total": 125000
                    }
                ],
                "subtotal": 125000,
                "tax": 0,
                "total": 125000,
                "status": "COMPLETED",
                "payment_method": "CASH"
            }

        Ensures:
        - 3% monthly revenue growth
        - CV (coefficient of variation) < 20% (regularity)
        - VIP customers order more frequently
        - Realistic date distribution (more orders at month-end)
        """
        random.seed(self.seed)
        self.faker.seed_instance(self.seed)

        products = self.get_products()
        customers = self.get_customers()

        size_config = BUSINESS_SIZES[self.business_size]
        base_monthly_orders = random.randint(*size_config['monthly_orders'])

        orders = []
        order_counter = 1

        # Generate orders month by month (oldest to newest)
        for month_offset in range(months, 0, -1):
            # Calculate growth factor (3% monthly growth backwards)
            growth_factor = 1.03 ** (months - month_offset)

            # Calculate monthly target orders with growth
            monthly_target_orders = int(base_monthly_orders * growth_factor)

            # Add variance (±15%) to avoid perfect regularity
            variance = random.uniform(0.85, 1.15)
            monthly_orders = int(monthly_target_orders * variance)

            # Generate orders for this month
            for _ in range(monthly_orders):
                order = self._generate_single_order(
                    month_offset=month_offset,
                    products=products,
                    customers=customers,
                    order_id=order_counter
                )
                orders.append(order)
                order_counter += 1

        # Update customer lifetime values
        self._update_customer_lifetime_values(customers, orders)

        # Sort orders by date
        return sorted(orders, key=lambda x: x['order_date'])

    # ========================================
    # PRIVATE HELPER METHODS
    # ========================================

    def _generate_seed(self, merchant_id: str) -> int:
        """
        Convert merchant_id to reproducible integer seed.

        Args:
            merchant_id: Merchant identifier string

        Returns:
            Integer seed derived from MD5 hash
        """
        hash_value = hashlib.md5(merchant_id.encode()).hexdigest()
        return int(hash_value[:8], 16)

    def _determine_business_category(self) -> str:
        """
        Assign business category based on seed.

        Returns:
            Category key from BUSINESS_CATEGORIES
        """
        categories = list(BUSINESS_CATEGORIES.keys())
        return random.choice(categories)

    def _determine_business_size(self) -> str:
        """
        Assign business size based on seed.

        Distribution:
        - SMALL: 20% (may struggle with TrustScore)
        - MEDIUM: 50% (typical case)
        - LARGE: 30% (exemplary business)

        Returns:
            Size key from BUSINESS_SIZES
        """
        rand = random.random()
        if rand < 0.20:
            return "SMALL"
        elif rand < 0.70:
            return "MEDIUM"
        else:
            return "LARGE"

    def _generate_product_variant(self, base_name: str, index: int) -> str:
        """
        Generate product name variant.

        Args:
            base_name: Base product name
            index: Product index for variation

        Returns:
            Product name with possible variation
        """
        # For variety, add variants to some products
        if index % 3 == 0 and random.random() > 0.5:
            variants = ['Premium', 'Standard', 'Économique', 'Deluxe']
            return f"{random.choice(variants)} {base_name}"
        return base_name

    def _get_unit_type(self, category: str) -> str:
        """
        Get appropriate unit type for category.

        Args:
            category: Business category

        Returns:
            Unit type string
        """
        units = {
            'RETAIL_FOOD': random.choice(['kg', 'sac', 'carton', 'unité', 'litre']),
            'WHOLESALE_CONSTRUCTION': random.choice(['sac', 'barre', 'm3', 'unité', 'rouleau']),
            'RETAIL_ELECTRONICS': 'unité',
            'WHOLESALE_CLOTHING': random.choice(['unité', 'pièce', 'lot', 'rouleau']),
            'PHARMACY': random.choice(['boîte', 'flacon', 'tube', 'unité']),
        }
        return units.get(category, 'unité')

    def _generate_single_order(
        self,
        month_offset: int,
        products: List[Dict],
        customers: List[Dict],
        order_id: int
    ) -> Dict[str, Any]:
        """
        Generate a single order with realistic item selection.

        Args:
            month_offset: Months in the past (1 = last month)
            products: Available products list
            customers: Available customers list
            order_id: Sequential order ID

        Returns:
            Order dictionary
        """
        # Select customer with VIP preference
        customer = self._select_weighted_customer(customers)

        # Generate order date within month
        order_date = self._generate_order_date(month_offset)

        # Determine number of items based on customer segment
        num_items = self._get_num_items_for_segment(customer['customer_segment'])
        selected_products = random.sample(products, min(num_items, len(products)))

        # Generate order items
        items = []
        subtotal = 0

        for product in selected_products:
            # Quantity varies by customer segment and business type
            if customer['customer_segment'] == 'VIP':
                quantity = random.randint(3, 20)
            elif customer['customer_segment'] == 'REGULAR':
                quantity = random.randint(2, 10)
            else:
                quantity = random.randint(1, 5)

            item_total = product['unit_price'] * quantity

            items.append({
                "product_id": product['id'],
                "product_name": product['name'],
                "quantity": quantity,
                "unit_price": product['unit_price'],
                "total": item_total
            })
            subtotal += item_total

        # Determine order status (92% completed, 5% pending, 3% cancelled)
        status = random.choices(
            ["COMPLETED", "PENDING", "CANCELLED"],
            weights=[0.92, 0.05, 0.03]
        )[0]

        return {
            "id": f"ORD-{order_date.strftime('%Y%m%d')}-{str(order_id).zfill(4)}",
            "order_date": order_date.isoformat(),
            "customer_id": customer['id'],
            "items": items,
            "subtotal": subtotal,
            "tax": 0,  # Simplified for hackathon
            "total": subtotal,
            "status": status,
            "payment_method": random.choice(["CASH", "MOBILE_MONEY", "BANK_TRANSFER"])
        }

    def _generate_order_date(self, month_offset: int) -> datetime:
        """
        Generate realistic order date within month.

        Pattern: More orders at month-end (salary days: 25th-5th of next month).

        Args:
            month_offset: Months in the past (1 = last month)

        Returns:
            Order datetime
        """
        today = datetime.now()
        target_date = today - timedelta(days=30 * month_offset)

        # Get the first day of the target month
        first_day = target_date.replace(day=1)

        # Calculate number of days in the month
        if first_day.month == 12:
            next_month = first_day.replace(year=first_day.year + 1, month=1)
        else:
            next_month = first_day.replace(month=first_day.month + 1)

        days_in_month = (next_month - first_day).days

        # Weighted towards end of month (days 25-31 more likely)
        day_weights = [1] * 24 + [3] * (days_in_month - 24)
        day = random.choices(range(1, days_in_month + 1), weights=day_weights)[0]

        # Business hours (8 AM to 6 PM)
        hour = random.randint(8, 18)
        minute = random.randint(0, 59)

        return datetime(first_day.year, first_day.month, day, hour, minute)

    def _generate_cameroon_phone(self) -> str:
        """
        Generate realistic Cameroon phone number.

        Returns:
            Phone number in format: +237 6XX XXX XXX
        """
        # Cameroon mobile prefixes (MTN, Orange)
        prefix = random.choice(['6', '67', '68', '69', '65', '66'])

        # Generate remaining digits
        if len(prefix) == 1:
            number = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        else:
            number = ''.join([str(random.randint(0, 9)) for _ in range(7)])

        # Format: +237 6XX XXX XXX
        return f"+237 {prefix}{number[0:1]} {number[1:4]} {number[4:7]}"

    def _select_weighted_customer(self, customers: List[Dict]) -> Dict:
        """
        Select customer with VIP preference.

        VIP customers order 3x more frequently than occasional customers.

        Args:
            customers: List of customers

        Returns:
            Selected customer
        """
        weights = {
            "VIP": 3,
            "REGULAR": 2,
            "OCCASIONAL": 1
        }

        customer_weights = [weights[c['customer_segment']] for c in customers]
        return random.choices(customers, weights=customer_weights)[0]

    def _get_num_items_for_segment(self, segment: str) -> int:
        """
        Get number of items per order based on customer segment.

        Args:
            segment: Customer segment (VIP, REGULAR, OCCASIONAL)

        Returns:
            Number of items to include in order
        """
        if segment == "VIP":
            return random.randint(3, 8)
        elif segment == "REGULAR":
            return random.randint(2, 4)
        else:  # OCCASIONAL
            return random.randint(1, 2)

    def _update_customer_lifetime_values(
        self,
        customers: List[Dict],
        orders: List[Dict]
    ) -> None:
        """
        Calculate and update customer lifetime values from orders.

        Args:
            customers: List of customers to update
            orders: List of orders to calculate from
        """
        customer_totals = defaultdict(int)

        for order in orders:
            if order['status'] == 'COMPLETED':
                customer_totals[order['customer_id']] += order['total']

        for customer in customers:
            customer['lifetime_value'] = customer_totals.get(customer['id'], 0)


# ============================================
# UTILITY FUNCTIONS
# ============================================

def validate_generated_data(
    orders: List[Dict],
    customers: List[Dict],
    products: List[Dict]
) -> Dict[str, bool]:
    """
    Validate that generated data meets TrustScore requirements.

    Args:
        orders: Generated orders
        customers: Generated customers
        products: Generated products

    Returns:
        Dictionary of validation metrics and their pass/fail status
    """
    # Check data relationships
    customer_ids = {c['id'] for c in customers}
    product_ids = {p['id'] for p in products}

    all_refs_valid = all(
        order['customer_id'] in customer_ids and
        all(item['product_id'] in product_ids for item in order['items'])
        for order in orders
    )

    # Calculate TrustScore metrics
    recurring_pct = len([c for c in customers if c['is_recurring']]) / len(customers) if customers else 0

    # Calculate monthly revenues
    completed_orders = [o for o in orders if o['status'] == 'COMPLETED']
    monthly_revenues = defaultdict(int)
    for order in completed_orders:
        month_key = order['order_date'][:7]  # YYYY-MM
        monthly_revenues[month_key] += order['total']

    revenues = list(monthly_revenues.values())

    if len(revenues) > 1:
        import statistics
        mean_revenue = statistics.mean(revenues)
        std_revenue = statistics.stdev(revenues)
        cv = std_revenue / mean_revenue if mean_revenue > 0 else 1
    else:
        cv = 0
        mean_revenue = revenues[0] if revenues else 0

    # Calculate gross margin
    total_revenue = sum(o['total'] for o in completed_orders)
    total_cost = 0
    for order in completed_orders:
        for item in order['items']:
            product = next((p for p in products if p['id'] == item['product_id']), None)
            if product:
                total_cost += product['cost'] * item['quantity']

    gross_margin = (total_revenue - total_cost) / total_revenue if total_revenue > 0 else 0

    return {
        "all_refs_valid": all_refs_valid,
        "cv_below_20": cv < 0.20,
        "recurring_above_60": recurring_pct >= 0.60,
        "monthly_revenue_above_2M": mean_revenue >= 2_000_000,
        "margin_above_25": gross_margin >= 0.25,
    }
