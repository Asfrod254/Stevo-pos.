"""SQLite storage and business rules for the standalone STEVO POS."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


ROLES = ("admin", "manager", "cashier")
PASSWORD_ITERATIONS = 310_000
DEFAULT_PRODUCTS = (
    ("Cement 50kg", 78000, 42, "Building"),
    ("Paint White", 62000, 18, "Finishing"),
    ("Steel Rod", 145000, 9, "Metal"),
    ("Tiles", 95000, 33, "Flooring"),
    ("PVC Pipes", 43000, 66, "Plumbing"),
)
DEFAULT_SETTINGS = {
    "store_name": "STEVO POS Suite",
    "tax_enabled": "1",
    "tax_rate_bps": "1600",
}


class PosError(ValueError):
    """An expected validation or business-rule error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _password_record(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


class PosDatabase:
    def __init__(self, path: str | Path, seed: bool = True):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize(seed)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self, seed: bool) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_record TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('admin', 'manager', 'cashier')),
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL COLLATE NOCASE,
                    category TEXT NOT NULL DEFAULT 'General',
                    price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
                    stock INTEGER NOT NULL CHECK (stock >= 0),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'paid'
                        CHECK (status IN ('pending', 'paid', 'completed', 'cancelled')),
                    payment_method TEXT NOT NULL,
                    subtotal_cents INTEGER NOT NULL,
                    tax_cents INTEGER NOT NULL,
                    total_cents INTEGER NOT NULL,
                    amount_received_cents INTEGER NOT NULL,
                    change_cents INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS order_items (
                    id TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
                    product_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    unit_price_cents INTEGER NOT NULL,
                    subtotal_cents INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
                CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
                """
            )
            connection.executemany(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                DEFAULT_SETTINGS.items(),
            )
            if seed:
                if connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
                    connection.execute(
                        "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                        (str(uuid.uuid4()), "admin", _password_record("admin123"), "admin", utc_now()),
                    )
                if connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
                    now = utc_now()
                    connection.executemany(
                        "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)",
                        [
                            (str(uuid.uuid4()), name, category, price, stock, now, now)
                            for name, price, stock, category in DEFAULT_PRODUCTS
                        ],
                    )

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            user = connection.execute(
                "SELECT id, username, password_record, role, created_at FROM users WHERE username = ?",
                (username.strip(),),
            ).fetchone()
        if not user:
            return None
        salt_hex, _, digest_hex = user["password_record"].partition("$")
        if not salt_hex or not digest_hex:
            return None
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), PASSWORD_ITERATIONS
        ).hex()
        if not hmac.compare_digest(candidate, digest_hex):
            return None
        return {key: user[key] for key in ("id", "username", "role", "created_at")}

    def add_user(self, username: str, password: str, role: str) -> str:
        username = username.strip()
        if len(username) < 2:
            raise PosError("Username must be at least 2 characters.")
        if len(password) < 6:
            raise PosError("Password must be at least 6 characters.")
        if role not in ROLES:
            raise PosError("Choose a valid user role.")
        user_id = str(uuid.uuid4())
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                    (user_id, username, _password_record(password), role, utc_now()),
                )
        except sqlite3.IntegrityError as error:
            raise PosError("That username is already in use.") from error
        return user_id

    def list_users(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, username, role, created_at FROM users ORDER BY username COLLATE NOCASE"
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_user(self, user_id: str) -> None:
        with self._connect() as connection:
            user = connection.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return
            if user["role"] == "admin" and connection.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'admin'"
            ).fetchone()[0] <= 1:
                raise PosError("The last administrator cannot be removed.")
            connection.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def list_products(self, search: str = "") -> list[dict[str, Any]]:
        query = "%" + search.strip() + "%"
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM products WHERE name LIKE ? OR category LIKE ? ORDER BY name COLLATE NOCASE",
                (query, query),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_product(
        self, name: str, price_cents: int, stock: int, category: str = "General", product_id: str | None = None
    ) -> str:
        name = name.strip()
        if not name:
            raise PosError("Product name is required.")
        if price_cents < 0 or stock < 0:
            raise PosError("Price and stock cannot be negative.")
        now = utc_now()
        try:
            with self._connect() as connection:
                if product_id:
                    cursor = connection.execute(
                        "UPDATE products SET name = ?, category = ?, price_cents = ?, stock = ?, updated_at = ? WHERE id = ?",
                        (name, category.strip() or "General", price_cents, stock, now, product_id),
                    )
                    if cursor.rowcount == 0:
                        raise PosError("Product not found.")
                    return product_id
                product_id = str(uuid.uuid4())
                connection.execute(
                    "INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (product_id, name, category.strip() or "General", price_cents, stock, now, now),
                )
        except sqlite3.IntegrityError as error:
            raise PosError("A product with that name already exists.") from error
        return product_id

    def delete_product(self, product_id: str) -> None:
        try:
            with self._connect() as connection:
                cursor = connection.execute("DELETE FROM products WHERE id = ?", (product_id,))
                if cursor.rowcount == 0:
                    raise PosError("Product not found.")
        except sqlite3.IntegrityError as error:
            raise PosError("This product is in an order and cannot be deleted.") from error

    def create_order(
        self,
        customer_name: str,
        items: dict[str, int],
        payment_method: str,
        amount_received_cents: int,
        tax_rate_bps: int = 0,
        pending: bool = False,
    ) -> str:
        customer_name = customer_name.strip() or "Walk-in Customer"
        if not items:
            raise PosError("Add at least one item before checkout.")
        if not pending and payment_method not in ("Cash", "M-Pesa", "Card"):
            raise PosError("Choose a valid payment method.")
        if not 0 <= tax_rate_bps <= 10000:
            raise PosError("Tax rate must be between 0% and 100%.")

        order_id = str(uuid.uuid4())
        now = utc_now()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            prepared = []
            subtotal = 0
            for product_id, quantity in items.items():
                if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
                    raise PosError("Item quantities must be positive whole numbers.")
                product = connection.execute(
                    "SELECT id, name, price_cents, stock FROM products WHERE id = ?", (product_id,)
                ).fetchone()
                if not product:
                    raise PosError("A product in this cart no longer exists.")
                if product["stock"] < quantity:
                    raise PosError(f"Not enough stock for {product['name']} ({product['stock']} available).")
                line_total = product["price_cents"] * quantity
                subtotal += line_total
                prepared.append((product, quantity, line_total))

            tax = (subtotal * tax_rate_bps + 5000) // 10000
            total = subtotal + tax
            if pending:
                status = "pending"
                payment_method = "Pending"
                amount_received_cents = 0
            elif payment_method != "Cash":
                amount_received_cents = total
                status = "paid"
            else:
                status = "paid"
            if not pending and amount_received_cents < total:
                raise PosError("Amount received is less than the total due.")

            connection.execute(
                "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    order_id,
                    customer_name,
                    status,
                    payment_method,
                    subtotal,
                    tax,
                    total,
                    amount_received_cents,
                    amount_received_cents - total,
                    now,
                ),
            )
            for product, quantity, line_total in prepared:
                connection.execute(
                    "INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()), order_id, product["id"], product["name"], quantity,
                        product["price_cents"], line_total,
                    ),
                )
                connection.execute(
                    "UPDATE products SET stock = stock - ?, updated_at = ? WHERE id = ?",
                    (quantity, now, product["id"]),
                )
        return order_id

    def record_order_payment(self, order_id: str, payment_method: str, amount_received_cents: int) -> None:
        if payment_method not in ("Cash", "M-Pesa", "Card"):
            raise PosError("Choose a valid payment method.")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            order = connection.execute(
                "SELECT status, total_cents FROM orders WHERE id = ?", (order_id,)
            ).fetchone()
            if not order:
                raise PosError("Order not found.")
            if order["status"] not in ("pending", "cancelled"):
                raise PosError("Only pending or cancelled orders can receive payment.")
            if payment_method != "Cash":
                amount_received_cents = order["total_cents"]
            if amount_received_cents < order["total_cents"]:
                raise PosError("Amount received is less than the total due.")
            if order["status"] == "cancelled":
                items = connection.execute(
                    "SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,)
                ).fetchall()
                for item in items:
                    product = connection.execute(
                        "SELECT name, stock FROM products WHERE id = ?", (item["product_id"],)
                    ).fetchone()
                    if not product or product["stock"] < item["quantity"]:
                        name = product["name"] if product else "a product"
                        raise PosError(f"Not enough stock to reopen this order ({name}).")
                for item in items:
                    connection.execute(
                        "UPDATE products SET stock = stock - ?, updated_at = ? WHERE id = ?",
                        (item["quantity"], utc_now(), item["product_id"]),
                    )
            connection.execute(
                "UPDATE orders SET status = 'paid', payment_method = ?, amount_received_cents = ?, "
                "change_cents = ? WHERE id = ?",
                (payment_method, amount_received_cents, amount_received_cents - order["total_cents"], order_id),
            )

    def list_orders(self, search: str = "") -> list[dict[str, Any]]:
        query = "%" + search.strip() + "%"
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT o.*, COUNT(i.id) AS item_count
                FROM orders o LEFT JOIN order_items i ON i.order_id = o.id
                WHERE o.customer_name LIKE ? OR o.id LIKE ? OR o.status LIKE ?
                GROUP BY o.id ORDER BY o.created_at DESC
                """,
                (query, query, query),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            order = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not order:
                return None
            items = connection.execute(
                "SELECT * FROM order_items WHERE order_id = ? ORDER BY rowid", (order_id,)
            ).fetchall()
        result = dict(order)
        result["items"] = [dict(item) for item in items]
        return result

    def update_order_status(self, order_id: str, status: str) -> None:
        if status not in ("pending", "paid", "completed", "cancelled"):
            raise PosError("Choose a valid order status.")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            order = connection.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not order:
                raise PosError("Order not found.")
            current_status = order["status"]
            if current_status == status:
                return
            if current_status in ("pending", "cancelled") and status in ("paid", "completed"):
                raise PosError("Record payment before completing this order.")
            if current_status in ("paid", "completed") and status == "pending":
                raise PosError("Paid orders cannot be changed back to pending.")
            items = connection.execute(
                "SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,)
            ).fetchall()
            if current_status == "cancelled" and status == "pending":
                for item in items:
                    product = connection.execute(
                        "SELECT name, stock FROM products WHERE id = ?", (item["product_id"],)
                    ).fetchone()
                    if not product or product["stock"] < item["quantity"]:
                        name = product["name"] if product else "a product"
                        raise PosError(f"Not enough stock to reopen this order ({name}).")
                for item in items:
                    connection.execute(
                        "UPDATE products SET stock = stock - ?, updated_at = ? WHERE id = ?",
                        (item["quantity"], utc_now(), item["product_id"]),
                    )
                connection.execute(
                    "UPDATE orders SET status = 'pending', payment_method = 'Pending', "
                    "amount_received_cents = 0, change_cents = 0 WHERE id = ?",
                    (order_id,),
                )
                return
            if current_status != "cancelled" and status == "cancelled":
                for item in items:
                    connection.execute(
                        "UPDATE products SET stock = stock + ?, updated_at = ? WHERE id = ?",
                        (item["quantity"], utc_now(), item["product_id"]),
                    )
            connection.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))

    def get_settings(self) -> dict[str, str]:
        with self._connect() as connection:
            settings = dict(connection.execute("SELECT key, value FROM settings").fetchall())
        return {**DEFAULT_SETTINGS, **settings}

    def set_setting(self, key: str, value: str) -> None:
        if key not in DEFAULT_SETTINGS:
            raise PosError("Unknown setting.")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def dashboard_summary(self) -> dict[str, Any]:
        with self._connect() as connection:
            orders = connection.execute(
                "SELECT COUNT(*) AS count, COALESCE(SUM(total_cents), 0) AS sales "
                "FROM orders WHERE status IN ('paid', 'completed')"
            ).fetchone()
            today = connection.execute(
                "SELECT COALESCE(SUM(total_cents), 0) FROM orders "
                "WHERE status IN ('paid', 'completed') AND substr(created_at, 1, 10) = ?",
                (datetime.now(timezone.utc).date().isoformat(),),
            ).fetchone()[0]
            inventory = connection.execute(
                "SELECT COUNT(*) AS products, COALESCE(SUM(stock), 0) AS units, "
                "COALESCE(SUM(CASE WHEN stock <= 5 THEN 1 ELSE 0 END), 0) AS low_stock "
                "FROM products"
            ).fetchone()
            best_seller = connection.execute(
                 "SELECT product_name, SUM(quantity) AS sold FROM order_items "
                 "JOIN orders ON orders.id = order_items.order_id "
                 "WHERE orders.status IN ('paid', 'completed') "
                "GROUP BY product_id ORDER BY sold DESC LIMIT 1"
            ).fetchone()
            stock = connection.execute(
                "SELECT name, stock FROM products ORDER BY stock DESC, name LIMIT 6"
            ).fetchall()
            trend = connection.execute(
                "SELECT substr(created_at, 1, 10) AS day, SUM(total_cents) AS sales "
                "FROM orders WHERE status IN ('paid', 'completed') GROUP BY day "
                "ORDER BY day DESC LIMIT 7"
            ).fetchall()
        return {
            "sales_cents": orders["sales"],
            "today_cents": today,
            "order_count": orders["count"],
            "product_count": inventory["products"],
            "units_in_stock": inventory["units"],
            "low_stock_count": inventory["low_stock"],
            "best_seller": dict(best_seller) if best_seller else None,
            "stock": [dict(row) for row in stock],
            "trend": [dict(row) for row in reversed(trend)],
        }