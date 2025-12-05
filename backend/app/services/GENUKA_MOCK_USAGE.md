# GenukaAPIClientMock - Usage Guide

## Overview
The `GenukaAPIClientMock` class generates reproducible, realistic business data for SmartKYC hackathon demo.

## Quick Start

```python
from app.services.genuka_mock import GenukaAPIClientMock

# Initialize with merchant ID
client = GenukaAPIClientMock(merchant_id="merchant-123")

# Get data
products = client.get_products()      # 20-150 products
customers = client.get_customers()    # 50-400 customers
orders = client.get_orders(months=12) # 12 months of orders
```

## Reproducibility

Same merchant_id **always** generates the same data:

```python
# Client 1
client1 = GenukaAPIClientMock("merchant-123")
orders1 = client1.get_orders()

# Client 2 (same merchant_id)
client2 = GenukaAPIClientMock("merchant-123")
orders2 = client2.get_orders()

# orders1 == orders2 ✅ Always true!
```

## Business Profiles

The mock generates 5 different business types:

| Category | Products | Avg Margin | Avg Basket | Stock Rotation |
|----------|----------|------------|------------|----------------|
| **RETAIL_FOOD** | Rice, Oil, Flour, Sugar... | 28% | 25,000 FCFA | 10×/year |
| **WHOLESALE_CONSTRUCTION** | Cement, Iron, Gravel... | 22% | 450,000 FCFA | 6×/year |
| **RETAIL_ELECTRONICS** | Phones, Accessories... | 35% | 85,000 FCFA | 12×/year |
| **WHOLESALE_CLOTHING** | Fabrics, Clothes... | 32% | 120,000 FCFA | 8×/year |
| **PHARMACY** | Medications, Vitamins... | 30% | 15,000 FCFA | 15×/year |

Business size is also randomly assigned: SMALL (20%), MEDIUM (50%), LARGE (30%)

## Data Validation

The mock ensures all TrustScore metrics are met:

```python
from app.services.genuka_mock import validate_generated_data

products = client.get_products()
customers = client.get_customers()
orders = client.get_orders()

validation = validate_generated_data(orders, customers, products)
# {
#   "all_refs_valid": True,
#   "cv_below_20": True,             # Regularity < 20% CV
#   "recurring_above_60": True,       # 60%+ recurring customers
#   "monthly_revenue_above_2M": True, # Avg > 2M FCFA/month
#   "margin_above_25": True           # Gross margin > 25%
# }
```

## Integration with TrustScore Calculator

```python
from app.services.genuka_mock import GenukaAPIClientMock

def calculate_trustscore(merchant_id: str):
    # Get mock data
    genuka = GenukaAPIClientMock(merchant_id)
    orders = genuka.get_orders(months=12)
    customers = genuka.get_customers()
    products = genuka.get_products()

    # Calculate metrics
    monthly_revenues = calculate_monthly_revenues(orders)
    cv = coefficient_of_variation(monthly_revenues)
    recurring_pct = len([c for c in customers if c['is_recurring']]) / len(customers)

    # Determine mode
    if len(monthly_revenues) < 3:
        calculation_mode = "COLD_START"
    else:
        calculation_mode = "NORMAL"

    # Calculate score...
```

## Demo Profiles

Create 5 test profiles with different scores:

```python
profiles = [
    ("kouassi-distribution", "GOLD candidate - Large retail food business"),
    ("marie-import-export", "SILVER candidate - Medium wholesale"),
    ("abdou-trading", "BRONZE candidate - Small business"),
    ("jean-nouveau", "NEW - Just started, COLD_START mode"),
    ("sarah-premium", "PLATINUM candidate - Excellent metrics"),
]

for merchant_id, description in profiles:
    client = GenukaAPIClientMock(merchant_id)
    print(f"{merchant_id}: {description}")
    print(f"  Category: {client.business_category}")
    print(f"  Size: {client.business_size}")
```

## Data Structures

### Product Schema
```json
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
```

### Customer Schema
```json
{
  "id": "CUST-0045",
  "name": "Kouassi Jean",
  "email": "kouassi.jean@example.cm",
  "phone": "+237 622 345 678",
  "first_order_date": "2024-01-15",
  "total_orders": 25,
  "lifetime_value": 1250000,
  "is_recurring": true,
  "customer_segment": "VIP"
}
```

### Order Schema
```json
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
```

## Environment Configuration

Enable/disable in `.env`:

```bash
USE_MOCK_GENUKA=true   # Use mock for hackathon
# USE_MOCK_GENUKA=false  # Use real Genuka API (production)
```

## Performance

- **First call**: ~300ms (generates all data)
- **Subsequent calls**: <5ms (cached)
- **5 demo profiles**: <2 seconds total

## Test Validation

Run the test suite:

```bash
cd /home/quasars/Documents/smartkyc-hackathon/smartkyc/backend
python3 test_genuka_mock.py
```

Expected output: ✅ All 5 tests passed

---

**Generated**: December 2025
**For**: SmartKYC Hackathon Demo
**Author**: SmartKYC Innovators Team
