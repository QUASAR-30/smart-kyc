"""
Test script for GenukaAPIClientMock
Verifies reproducibility, data relationships, and TrustScore metrics
"""

import sys
sys.path.insert(0, '/home/quasars/Documents/smartkyc-hackathon/smartkyc/backend')

from app.services.genuka_mock import GenukaAPIClientMock, validate_generated_data


def test_reproducibility():
    """Test that same merchant_id generates identical data"""
    print("\n" + "="*60)
    print("TEST 1: Reproducibility")
    print("="*60)

    merchant_id = "test-merchant-123"

    # Generate data twice
    client1 = GenukaAPIClientMock(merchant_id)
    orders1 = client1.get_orders(months=12)
    customers1 = client1.get_customers()
    products1 = client1.get_products()

    client2 = GenukaAPIClientMock(merchant_id)
    orders2 = client2.get_orders(months=12)
    customers2 = client2.get_customers()
    products2 = client2.get_products()

    # Compare
    orders_match = orders1 == orders2
    customers_match = customers1 == customers2
    products_match = products1 == products2

    print(f"Orders match: {orders_match}")
    print(f"Customers match: {customers_match}")
    print(f"Products match: {products_match}")

    if orders_match and customers_match and products_match:
        print("✅ PASSED: Data is reproducible")
    else:
        print("❌ FAILED: Data is not reproducible")

    return orders_match and customers_match and products_match


def test_data_volume():
    """Test that data volume is appropriate"""
    print("\n" + "="*60)
    print("TEST 2: Data Volume")
    print("="*60)

    merchant_id = "test-merchant-456"
    client = GenukaAPIClientMock(merchant_id)

    products = client.get_products()
    customers = client.get_customers()
    orders = client.get_orders(months=12)

    print(f"Business Category: {client.business_category}")
    print(f"Business Size: {client.business_size}")
    print(f"Number of products: {len(products)}")
    print(f"Number of customers: {len(customers)}")
    print(f"Number of orders (12 months): {len(orders)}")

    # Check reasonable ranges
    products_ok = 20 <= len(products) <= 150
    customers_ok = 50 <= len(customers) <= 400
    orders_ok = 600 <= len(orders) <= 6000

    print(f"\nProducts in range (20-150): {products_ok}")
    print(f"Customers in range (50-400): {customers_ok}")
    print(f"Orders in range (600-6000): {orders_ok}")

    if products_ok and customers_ok and orders_ok:
        print("✅ PASSED: Data volume is appropriate")
        return True
    else:
        print("❌ FAILED: Data volume out of expected range")
        return False


def test_data_relationships():
    """Test that all references are valid"""
    print("\n" + "="*60)
    print("TEST 3: Data Relationships")
    print("="*60)

    merchant_id = "test-merchant-789"
    client = GenukaAPIClientMock(merchant_id)

    products = client.get_products()
    customers = client.get_customers()
    orders = client.get_orders(months=12)

    customer_ids = {c['id'] for c in customers}
    product_ids = {p['id'] for p in products}

    # Check all references
    invalid_orders = []
    for order in orders:
        if order['customer_id'] not in customer_ids:
            invalid_orders.append(f"Invalid customer_id: {order['customer_id']}")
        for item in order['items']:
            if item['product_id'] not in product_ids:
                invalid_orders.append(f"Invalid product_id: {item['product_id']}")

    if not invalid_orders:
        print(f"✅ PASSED: All {len(orders)} orders have valid references")
        return True
    else:
        print(f"❌ FAILED: Found {len(invalid_orders)} invalid references")
        for error in invalid_orders[:5]:  # Show first 5 errors
            print(f"  - {error}")
        return False


def test_trustscore_metrics():
    """Test that data satisfies TrustScore requirements"""
    print("\n" + "="*60)
    print("TEST 4: TrustScore Metrics")
    print("="*60)

    merchant_id = "test-merchant-gold"
    client = GenukaAPIClientMock(merchant_id)

    products = client.get_products()
    customers = client.get_customers()
    orders = client.get_orders(months=12)

    # Validate data
    validation = validate_generated_data(orders, customers, products)

    print("\nValidation Results:")
    for metric, passed in validation.items():
        status = "✅" if passed else "❌"
        print(f"{status} {metric}: {passed}")

    # Calculate and display actual metrics
    recurring_count = len([c for c in customers if c['is_recurring']])
    recurring_pct = recurring_count / len(customers) * 100

    print(f"\nDetailed Metrics:")
    print(f"Recurring customers: {recurring_count}/{len(customers)} ({recurring_pct:.1f}%)")

    # Monthly revenues
    from collections import defaultdict
    monthly_revenues = defaultdict(int)
    completed_orders = [o for o in orders if o['status'] == 'COMPLETED']

    for order in completed_orders:
        month_key = order['order_date'][:7]
        monthly_revenues[month_key] += order['total']

    revenues = list(monthly_revenues.values())
    if len(revenues) > 1:
        import statistics
        mean_revenue = statistics.mean(revenues)
        std_revenue = statistics.stdev(revenues)
        cv = std_revenue / mean_revenue if mean_revenue > 0 else 1
        print(f"Coefficient of Variation: {cv:.2%}")
        print(f"Average monthly revenue: {mean_revenue:,.0f} FCFA")

    # Gross margin
    total_revenue = sum(o['total'] for o in completed_orders)
    total_cost = 0
    for order in completed_orders:
        for item in order['items']:
            product = next((p for p in products if p['id'] == item['product_id']), None)
            if product:
                total_cost += product['cost'] * item['quantity']

    gross_margin = (total_revenue - total_cost) / total_revenue if total_revenue > 0 else 0
    print(f"Gross margin: {gross_margin:.1%}")

    all_passed = all(validation.values())
    if all_passed:
        print("\n✅ PASSED: All TrustScore metrics meet requirements")
    else:
        print("\n❌ FAILED: Some TrustScore metrics below requirements")

    return all_passed


def test_sample_data():
    """Display sample data for inspection"""
    print("\n" + "="*60)
    print("TEST 5: Sample Data Display")
    print("="*60)

    merchant_id = "demo-merchant"
    client = GenukaAPIClientMock(merchant_id)

    products = client.get_products()
    customers = client.get_customers()
    orders = client.get_orders(months=3)  # Just 3 months for display

    print(f"\nBusiness Profile:")
    print(f"  Category: {client.business_category}")
    print(f"  Size: {client.business_size}")

    print(f"\nSample Products (first 3):")
    for product in products[:3]:
        margin = (product['unit_price'] - product['cost']) / product['unit_price'] * 100
        print(f"  - {product['name']}")
        print(f"    Price: {product['unit_price']:,} FCFA, Margin: {margin:.1f}%")

    print(f"\nSample Customers (first 3):")
    for customer in customers[:3]:
        print(f"  - {customer['name']} ({customer['customer_segment']})")
        print(f"    Phone: {customer['phone']}, Orders: {customer['total_orders']}")

    print(f"\nSample Orders (first 3):")
    for order in orders[:3]:
        print(f"  - {order['id']}")
        print(f"    Date: {order['order_date']}, Total: {order['total']:,} FCFA")
        print(f"    Items: {len(order['items'])}, Status: {order['status']}")

    print("\n✅ PASSED: Sample data displayed successfully")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("GENUKA MOCK API - TEST SUITE")
    print("="*60)

    results = []

    results.append(("Reproducibility", test_reproducibility()))
    results.append(("Data Volume", test_data_volume()))
    results.append(("Data Relationships", test_data_relationships()))
    results.append(("TrustScore Metrics", test_trustscore_metrics()))
    results.append(("Sample Data", test_sample_data()))

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed! GenukaAPIClientMock is working correctly.")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Please review.")


if __name__ == "__main__":
    run_all_tests()
