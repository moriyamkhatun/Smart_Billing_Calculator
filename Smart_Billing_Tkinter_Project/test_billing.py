import unittest
from decimal import Decimal
from smart_billing_app import CartItem, calculate_bill, validate_item


class BillingTests(unittest.TestCase):
    def setUp(self):
        self.items = [
            CartItem("Notebook", "Stationery", Decimal("40.00"), 2),
            CartItem("Pen set", "Stationery", Decimal("60.00"), 1),
            CartItem("Bottle", "Accessories", Decimal("160.00"), 1),
        ]

    def test_no_discount(self):
        result = calculate_bill(self.items)
        self.assertEqual(result["subtotal"], Decimal("300.00"))
        self.assertEqual(result["discount"], Decimal("0.00"))
        self.assertEqual(result["net_payable"], Decimal("300.00"))

    def test_percentage_discount(self):
        result = calculate_bill(self.items, "Percentage", Decimal("10"))
        self.assertEqual(result["discount"], Decimal("30.00"))
        self.assertEqual(result["net_payable"], Decimal("270.00"))

    def test_fixed_discount(self):
        result = calculate_bill(self.items, "Fixed Amount", Decimal("50"))
        self.assertEqual(result["discount"], Decimal("50.00"))
        self.assertEqual(result["net_payable"], Decimal("250.00"))

    def test_fixed_discount_cannot_exceed_subtotal(self):
        result = calculate_bill(self.items, "Fixed Amount", Decimal("500"))
        self.assertEqual(result["discount"], Decimal("300.00"))
        self.assertEqual(result["net_payable"], Decimal("0.00"))

    def test_percentage_over_100_rejected(self):
        with self.assertRaises(ValueError):
            calculate_bill(self.items, "Percentage", Decimal("101"))

    def test_negative_discount_rejected(self):
        with self.assertRaises(ValueError):
            calculate_bill(self.items, "Fixed Amount", Decimal("-5"))

    def test_invalid_item_rejected(self):
        with self.assertRaises(ValueError):
            validate_item("", "General", Decimal("10"), 1)
        with self.assertRaises(ValueError):
            validate_item("Pen", "General", Decimal("-1"), 1)
        with self.assertRaises(ValueError):
            validate_item("Pen", "General", Decimal("1"), 0)


if __name__ == "__main__":
    unittest.main()
