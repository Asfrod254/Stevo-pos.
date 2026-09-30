import tempfile
import unittest
from pathlib import Path

from pos_db import PosDatabase, PosError


class PosDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = PosDatabase(Path(self.temp_dir.name) / "test.sqlite3")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_demo_admin_and_seed_products_are_available(self):
        user = self.database.authenticate("admin", "admin123")
        self.assertEqual(user["role"], "admin")
        self.assertIsNone(self.database.authenticate("admin", "wrong-password"))
        self.assertEqual(len(self.database.list_products()), 5)

    def test_sale_is_persisted_and_deducts_stock_atomically(self):
        product = self.database.list_products()[0]
        order_id = self.database.create_order(
            "Customer", {product["id"]: 2}, "Cash", 200000, tax_rate_bps=0
        )
        order = self.database.get_order(order_id)
        self.assertEqual(order["status"], "paid")
        self.assertEqual(order["total_cents"], product["price_cents"] * 2)
        self.assertEqual(order["change_cents"], 200000 - order["total_cents"])
        updated = next(row for row in self.database.list_products() if row["id"] == product["id"])
        self.assertEqual(updated["stock"], product["stock"] - 2)

    def test_insufficient_stock_leaves_order_and_stock_unchanged(self):
        product = self.database.list_products()[0]
        with self.assertRaisesRegex(PosError, "Not enough stock"):
            self.database.create_order(
                "Customer", {product["id"]: product["stock"] + 1}, "M-Pesa", 0
            )
        self.assertEqual(self.database.list_orders(), [])
        updated = next(row for row in self.database.list_products() if row["id"] == product["id"])
        self.assertEqual(updated["stock"], product["stock"])

    def test_checkout_calculates_tax_and_enforces_payment(self):
        product = self.database.list_products()[0]
        subtotal = product["price_cents"]
        total = subtotal + (subtotal * 1600 + 5000) // 10000
        with self.assertRaisesRegex(PosError, "less than the total"):
            self.database.create_order("", {product["id"]: 1}, "Cash", total - 1, 1600)
        self.database.create_order("", {product["id"]: 1}, "Cash", total, 1600)
        order = self.database.list_orders()[0]
        self.assertEqual(order["tax_cents"], total - subtotal)
        self.assertEqual(order["customer_name"], "Walk-in Customer")

    def test_user_roles_and_last_admin_guard(self):
        with self.assertRaisesRegex(PosError, "last administrator"):
            self.database.delete_user(self.database.list_users()[0]["id"])
        self.database.add_user("cashier", "cashier123", "cashier")
        self.assertEqual(self.database.authenticate("CASHIER", "cashier123")["role"], "cashier")

    def test_product_referenced_by_sale_cannot_be_deleted(self):
        product = self.database.list_products()[0]
        self.database.create_order("Customer", {product["id"]: 1}, "Card", 0)
        with self.assertRaisesRegex(PosError, "in an order"):
            self.database.delete_product(product["id"])

    def test_cancelling_and_restoring_order_reconciles_inventory(self):
        product = self.database.list_products()[0]
        order_id = self.database.create_order("Customer", {product["id"]: 3}, "Card", 0)
        self.database.update_order_status(order_id, "cancelled")
        restored_stock = next(row for row in self.database.list_products() if row["id"] == product["id"])
        self.assertEqual(restored_stock["stock"], product["stock"])
        self.database.record_order_payment(order_id, "Card", 0)
        reserved_stock = next(row for row in self.database.list_products() if row["id"] == product["id"])
        self.assertEqual(reserved_stock["stock"], product["stock"] - 3)

    def test_dashboard_summary_reports_sales_and_best_seller(self):
        product = self.database.list_products()[0]
        order_id = self.database.create_order("Customer", {product["id"]: 2}, "Card", 0)
        summary = self.database.dashboard_summary()
        self.assertEqual(summary["order_count"], 1)
        self.assertEqual(summary["sales_cents"], product["price_cents"] * 2)
        self.assertEqual(summary["best_seller"], {"product_name": product["name"], "sold": 2})
        self.assertEqual(self.database.get_order(order_id)["status"], "paid")

    def test_pending_order_reserves_stock_and_requires_payment(self):
        product = self.database.list_products()[0]
        order_id = self.database.create_order(
            "Customer", {product["id"]: 2}, "Pending", 0, pending=True
        )
        order = self.database.get_order(order_id)
        self.assertEqual(order["status"], "pending")
        self.assertEqual(order["payment_method"], "Pending")
        self.assertEqual(order["amount_received_cents"], 0)
        self.assertEqual(self.database.dashboard_summary()["sales_cents"], 0)
        updated = next(row for row in self.database.list_products() if row["id"] == product["id"])
        self.assertEqual(updated["stock"], product["stock"] - 2)
        with self.assertRaisesRegex(PosError, "Record payment"):
            self.database.update_order_status(order_id, "paid")
        with self.assertRaisesRegex(PosError, "less than the total"):
            self.database.record_order_payment(order_id, "Cash", order["total_cents"] - 1)
        self.database.record_order_payment(order_id, "Cash", order["total_cents"] + 500)
        paid_order = self.database.get_order(order_id)
        self.assertEqual(paid_order["status"], "paid")
        self.assertEqual(paid_order["change_cents"], 500)

    def test_cancelling_pending_order_releases_reserved_stock(self):
        product = self.database.list_products()[0]
        order_id = self.database.create_order(
            "Customer", {product["id"]: 2}, "Pending", 0, pending=True
        )
        self.database.update_order_status(order_id, "cancelled")
        restored = next(row for row in self.database.list_products() if row["id"] == product["id"])
        self.assertEqual(restored["stock"], product["stock"])
        self.database.update_order_status(order_id, "pending")
        reserved = next(row for row in self.database.list_products() if row["id"] == product["id"])
        self.assertEqual(reserved["stock"], product["stock"] - 2)
        self.assertEqual(self.database.get_order(order_id)["payment_method"], "Pending")
        paid_id = self.database.create_order("Paid", {product["id"]: 1}, "Card", 0)
        with self.assertRaisesRegex(PosError, "Paid orders cannot"):
            self.database.update_order_status(paid_id, "pending")


if __name__ == "__main__":
    unittest.main()