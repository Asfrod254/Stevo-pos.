"""Standalone, offline desktop point-of-sale application."""

from __future__ import annotations

import csv
import os
import tkinter as tk
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from pos_db import PosDatabase, PosError


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
DATABASE_PATH = DATA_DIR / "stevo_pos.sqlite3"
PAGE_ROLES = {
    "Overview": {"admin", "manager", "cashier"},
    "Products": {"admin", "manager", "cashier"},
    "Orders": {"admin", "manager", "cashier"},
    "Reports": {"admin", "manager"},
    "Settings": {"admin"},
    "Users": {"admin"},
}
NAV_ITEMS = ("Overview", "Products", "Orders", "Reports", "Settings", "Users")
BG = "#f1f3ee"
PANEL = "#ffffff"
INK = "#1d2926"
MUTED = "#70807a"
LINE = "#dce3dd"
GREEN = "#197553"
GREEN_DARK = "#125940"
GREEN_PALE = "#e3f1e9"
AMBER = "#bd7722"
RED = "#a84538"


def money(cents: int) -> str:
    return f"Ksh {Decimal(cents) / 100:,.2f}"


def parse_cents(value: str) -> int:
    try:
        amount = Decimal(value.strip()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, AttributeError):
        raise PosError("Enter a valid amount.") from None
    if not amount.is_finite() or amount < 0:
        raise PosError("Amount must be zero or greater.")
    return int(amount * 100)


class OfflinePos:
    def __init__(self, root: tk.Tk, database: PosDatabase):
        self.root = root
        self.database = database
        self.user: dict[str, Any] | None = None
        self.page = "Overview"
        self.cart: dict[str, int] = {}
        self.selected_order_id: str | None = None
        self.show_pending_only = False
        self.search_entry: ttk.Entry | None = None
        self.shell: ttk.Frame | None = None
        self.content: ttk.Frame | None = None
        self.style = ttk.Style(root)
        self._configure_window()
        self.show_login()

    def _configure_window(self) -> None:
        self.root.title("STEVO POS | Offline Point of Sale")
        self.root.geometry("1320x820")
        self.root.minsize(1080, 680)
        self.root.configure(background=BG)
        self.style.theme_use("clam")
        self.style.configure("TFrame", background=BG)
        self.style.configure("Panel.TFrame", background=PANEL)
        self.style.configure("TLabel", background=BG, foreground=INK, font=("Segoe UI", 10))
        self.style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 9))
        self.style.configure("Title.TLabel", background=BG, foreground=INK, font=("Segoe UI", 24, "bold"))
        self.style.configure("Section.TLabel", background=BG, foreground=INK, font=("Segoe UI", 13, "bold"))
        self.style.configure("CardValue.TLabel", background=PANEL, foreground=INK, font=("Segoe UI", 22, "bold"))
        self.style.configure("CardLabel.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 9, "bold"))
        self.style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
        self.style.configure("Primary.TButton", background=GREEN, foreground="white", borderwidth=0)
        self.style.map("Primary.TButton", background=[("active", GREEN_DARK), ("disabled", "#aabbb2")])
        self.style.configure("Soft.TButton", background=GREEN_PALE, foreground=GREEN_DARK, borderwidth=0)
        self.style.configure("Danger.TButton", background="#f8e9e5", foreground=RED, borderwidth=0)
        self.style.configure("Nav.TButton", anchor="w", background="#18362e", foreground="#d0ded7", borderwidth=0, padding=(16, 12))
        self.style.map("Nav.TButton", background=[("active", "#254b3e")], foreground=[("active", "white")])
        self.style.configure("SelectedNav.TButton", anchor="w", background="#287858", foreground="white", borderwidth=0, padding=(16, 12))
        self.style.configure(
            "Treeview", background=PANEL, fieldbackground=PANEL, foreground=INK,
            rowheight=34, borderwidth=0, font=("Segoe UI", 9),
        )
        self.style.configure("Treeview.Heading", background="#edf1ec", foreground=MUTED, relief="flat", font=("Segoe UI", 9, "bold"))
        self.style.map("Treeview", background=[("selected", GREEN_PALE)], foreground=[("selected", GREEN_DARK)])
        self.style.configure("TEntry", padding=(9, 7), fieldbackground="white")
        self.style.configure("TCombobox", padding=(8, 7), fieldbackground="white")
        self.style.configure("TLabelframe", background=BG, foreground=INK)
        self.style.configure("TLabelframe.Label", background=BG, foreground=MUTED, font=("Segoe UI", 9, "bold"))
        self.root.bind("<Escape>", lambda _event: self.root.focus_set())
        self.root.bind_all("<F1>", self.show_shortcuts)
        self.root.bind_all("<F2>", self.start_new_order)
        self.root.bind_all("<F5>", lambda _event: self.show_main() if self.user else None)
        self.root.bind_all("<Control-n>", self.start_new_order)
        self.root.bind_all("<Control-o>", lambda _event: self.go("Orders") if self.user else None)
        self.root.bind_all("<Control-r>", lambda _event: self.go("Reports") if self.user else None)
        self.root.bind_all("<Control-f>", self.focus_search)
        self.root.bind_all("<Control-Shift-p>", self.shortcut_add_product)

    def show_shortcuts(self, _event: tk.Event[Any] | None = None) -> str:
        messagebox.showinfo(
            "Keyboard shortcuts",
            "F1   Shortcut help\n"
            "F2 or Ctrl+N   Add a new order\n"
            "Ctrl+Shift+P   Add a product\n"
            "Ctrl+O   Open orders\n"
            "Ctrl+R   Open reports\n"
            "Ctrl+F   Focus the current search\n"
            "F5   Refresh the current screen",
            parent=self.root,
        )
        return "break"

    def focus_search(self, _event: tk.Event[Any] | None = None) -> str:
        if self.search_entry and self.search_entry.winfo_exists():
            self.search_entry.focus_set()
            self.search_entry.selection_range(0, "end")
        return "break"

    def shortcut_add_product(self, _event: tk.Event[Any] | None = None) -> str:
        if self.user and self.user["role"] in ("admin", "manager"):
            self.add_product()
        return "break"

    def show_login(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()
        page = ttk.Frame(self.root, padding=36)
        page.place(relx=0.5, rely=0.5, anchor="center")
        panel = tk.Frame(page, bg=PANEL, padx=42, pady=36, highlightthickness=1, highlightbackground=LINE)
        panel.grid()
        tk.Label(panel, text="STEVO", font=("Segoe UI", 13, "bold"), fg=GREEN, bg=PANEL).grid(sticky="w")
        tk.Label(panel, text="Point of sale", font=("Segoe UI", 26, "bold"), fg=INK, bg=PANEL).grid(row=1, sticky="w", pady=(4, 0))
        tk.Label(panel, text="Works offline. Your sales stay on this device.", font=("Segoe UI", 10), fg=MUTED, bg=PANEL).grid(row=2, sticky="w", pady=(4, 24))
        tk.Label(panel, text="USERNAME", font=("Segoe UI", 8, "bold"), fg=MUTED, bg=PANEL).grid(row=3, sticky="w")
        username = ttk.Entry(panel, width=34)
        username.grid(row=4, sticky="ew", pady=(5, 15))
        username.insert(0, "admin")
        tk.Label(panel, text="PASSWORD", font=("Segoe UI", 8, "bold"), fg=MUTED, bg=PANEL).grid(row=5, sticky="w")
        password = ttk.Entry(panel, width=34, show="•")
        password.grid(row=6, sticky="ew", pady=(5, 18))
        error = tk.StringVar()
        tk.Label(panel, textvariable=error, font=("Segoe UI", 9), fg=RED, bg=PANEL, wraplength=290, justify="left").grid(row=7, sticky="w", pady=(0, 9))

        def login(_event: tk.Event[Any] | None = None) -> None:
            account = self.database.authenticate(username.get(), password.get())
            if not account:
                error.set("Username or password is incorrect.")
                password.focus_set()
                return
            self.user = account
            self.page = "Overview"
            self.show_main()

        ttk.Button(panel, text="Sign in", command=login, style="Primary.TButton").grid(row=8, sticky="ew")
        tk.Label(panel, text="First run demo login: admin / admin123", font=("Segoe UI", 9), fg=MUTED, bg=PANEL).grid(row=9, sticky="w", pady=(15, 0))
        password.bind("<Return>", login)
        username.bind("<Return>", lambda _event: password.focus_set())
        username.focus_set()

    def show_main(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()
        self.shell = ttk.Frame(self.root)
        self.shell.pack(fill="both", expand=True)
        sidebar = tk.Frame(self.shell, bg="#18362e", width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="STEVO", font=("Segoe UI", 18, "bold"), fg="white", bg="#18362e").pack(anchor="w", padx=22, pady=(27, 1))
        tk.Label(sidebar, text="OFFLINE POINT OF SALE", font=("Segoe UI", 8, "bold"), fg="#a5c1b3", bg="#18362e").pack(anchor="w", padx=23, pady=(0, 25))
        for item in NAV_ITEMS:
            if self.user["role"] not in PAGE_ROLES[item]:
                continue
            ttk.Button(
                sidebar, text=item, style="SelectedNav.TButton" if item == self.page else "Nav.TButton",
                command=lambda page=item: self.go(page),
            ).pack(fill="x", padx=12, pady=2)
        tk.Frame(sidebar, bg="#36564b", height=1).pack(fill="x", padx=18, pady=(24, 14))
        tk.Label(sidebar, text="LOCAL DATABASE", font=("Segoe UI", 8, "bold"), fg="#a5c1b3", bg="#18362e").pack(anchor="w", padx=22)
        tk.Label(sidebar, text="Saved on this computer", font=("Segoe UI", 9), fg="white", bg="#18362e").pack(anchor="w", padx=22, pady=(4, 0))

        main = ttk.Frame(self.shell)
        main.pack(side="left", fill="both", expand=True)
        header = tk.Frame(main, bg=PANEL, height=66, highlightthickness=1, highlightbackground=LINE)
        header.pack(fill="x")
        header.pack_propagate(False)
        store_name = self.database.get_settings()["store_name"]
        tk.Label(header, text=store_name, font=("Segoe UI", 10, "bold"), fg=INK, bg=PANEL).pack(side="left", padx=24)
        tk.Label(header, text="●  OFFLINE", font=("Segoe UI", 8, "bold"), fg=GREEN, bg=GREEN_PALE, padx=10, pady=5).pack(side="left")
        pending_count = sum(order["status"] == "pending" for order in self.database.list_orders())
        ttk.Button(
            header,
            text=f"Pending orders  {pending_count}" if pending_count else "No pending orders",
            command=self.open_pending_orders,
            style="Danger.TButton" if pending_count else "Soft.TButton",
        ).pack(side="right", padx=(0, 20))
        account = tk.Frame(header, bg=PANEL)
        account.pack(side="right", padx=20)
        tk.Label(account, text=self.user["username"], font=("Segoe UI", 9, "bold"), fg=INK, bg=PANEL).pack(side="left", padx=(0, 10))
        ttk.Button(account, text="Sign out", command=self.sign_out, style="Soft.TButton").pack(side="left")
        self.content = ttk.Frame(main, padding=(26, 21))
        self.content.pack(fill="both", expand=True)
        self._render_page()

    def go(self, page: str) -> None:
        if not self.user or self.user["role"] not in PAGE_ROLES[page]:
            return
        self.page = page
        self.show_main()

    def open_pending_orders(self) -> None:
        self.show_pending_only = True
        self.go("Orders")

    def start_new_order(self, _event: tk.Event[Any] | None = None) -> str:
        if not self.user:
            return "break"
        self.show_pending_only = False
        if self.page != "Orders":
            self.page = "Orders"
            self.show_main()
        dialog = OrderEntryDialog(self.root, self.database, self.user["role"])
        self.root.wait_window(dialog)
        if dialog.result:
            order_id = dialog.result["order_id"]
            self.selected_order_id = order_id
            self.show_pending_only = dialog.result["status"] == "pending"
            self.show_main()
            if dialog.result["status"] == "pending":
                messagebox.showinfo("Order saved", "Order held for payment. Its items are reserved from stock.")
            else:
                self.show_receipt(order_id)
        return "break"

    def sign_out(self) -> None:
        if self.cart and not messagebox.askyesno("Discard cart?", "Signing out will discard the current cart."):
            return
        self.cart.clear()
        self.user = None
        self.show_login()

    def _clear_content(self) -> ttk.Frame:
        for child in self.content.winfo_children():
            child.destroy()
        return self.content

    def _page_heading(self, parent: ttk.Frame, title: str, subtitle: str, action: tuple[str, Any] | None = None) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(0, 18))
        left = ttk.Frame(row)
        left.pack(side="left", fill="x", expand=True)
        ttk.Label(left, text=title, style="Title.TLabel").pack(anchor="w")
        ttk.Label(left, text=subtitle, style="Muted.TLabel").pack(anchor="w", pady=(3, 0))
        if action:
            ttk.Button(row, text=action[0], command=action[1], style="Primary.TButton").pack(side="right", anchor="center")

    def _panel(self, parent: tk.Misc, padding: int = 15) -> tk.Frame:
        return tk.Frame(parent, bg=PANEL, padx=padding, pady=padding, highlightthickness=1, highlightbackground=LINE)

    def _tree(
        self, parent: tk.Misc, columns: tuple[str, ...], headings: tuple[str, ...],
        widths: tuple[int, ...], height: int = 12,
    ) -> ttk.Treeview:
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=height, selectmode="browse")
        for column, heading, width in zip(columns, headings, widths):
            tree.heading(column, text=heading)
            tree.column(column, width=width, minwidth=65, anchor="w" if column in ("name", "customer", "status", "product") else "center", stretch=True)
        scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def _render_page(self) -> None:
        if self.page == "Overview":
            self.render_overview()
        elif self.page == "Products":
            self.render_products()
        elif self.page == "Orders":
            self.render_orders()
        elif self.page == "Reports":
            self.render_reports()
        elif self.page == "Settings":
            self.render_settings()
        elif self.page == "Users":
            self.render_users()

    def render_overview(self) -> None:
        parent = self._clear_content()
        self._page_heading(parent, "Overview", "Live totals from sales saved on this device.", ("New order", self.start_new_order))
        pending_orders = [order for order in self.database.list_orders() if order["status"] == "pending"]
        if pending_orders:
            notice = tk.Frame(parent, bg="#fff2dc", padx=14, pady=10)
            notice.pack(fill="x", pady=(0, 14))
            tk.Label(notice, text=f"{len(pending_orders)} order{'s' if len(pending_orders) != 1 else ''} awaiting payment", font=("Segoe UI", 10, "bold"), fg="#81500f", bg="#fff2dc").pack(side="left")
            ttk.Button(notice, text="Review pending", command=self.open_pending_orders, style="Soft.TButton").pack(side="right")
        summary = self.database.dashboard_summary()
        cards = ttk.Frame(parent)
        cards.pack(fill="x", pady=(0, 16))
        values = (
            ("TODAY'S SALES", money(summary["today_cents"]), "Paid and completed orders"),
            ("ALL-TIME SALES", money(summary["sales_cents"]), f"{summary['order_count']} paid orders"),
            ("PRODUCTS", str(summary["product_count"]), f"{summary['units_in_stock']:,} units available"),
            ("LOW STOCK", str(summary["low_stock_count"]), "Items at 5 units or less"),
        )
        for index, (label, value, note) in enumerate(values):
            card = self._panel(cards, 16)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 7, 7 if index < 3 else 0))
            ttk.Label(card, text=label, style="CardLabel.TLabel").pack(anchor="w")
            ttk.Label(card, text=value, style="CardValue.TLabel").pack(anchor="w", pady=(8, 5))
            tk.Label(card, text=note, font=("Segoe UI", 9), fg=MUTED, bg=PANEL).pack(anchor="w")
            cards.columnconfigure(index, weight=1)

        mid = ttk.Frame(parent)
        mid.pack(fill="both", expand=True, pady=(0, 15))
        stock_panel = self._panel(mid)
        stock_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(stock_panel, text="Stock on hand", font=("Segoe UI", 13, "bold"), fg=INK, bg=PANEL).pack(anchor="w")
        tk.Label(stock_panel, text="Highest available quantities", font=("Segoe UI", 9), fg=MUTED, bg=PANEL).pack(anchor="w", pady=(2, 11))
        stock_canvas = tk.Canvas(stock_panel, bg=PANEL, highlightthickness=0, height=230)
        stock_canvas.pack(fill="both", expand=True)
        stock_rows = summary["stock"]
        max_stock = max((row["stock"] for row in stock_rows), default=1) or 1
        for index, row in enumerate(stock_rows):
            y = 13 + index * 34
            stock_canvas.create_text(0, y + 7, text=row["name"][:23], anchor="w", fill=INK, font=("Segoe UI", 9))
            stock_canvas.create_rectangle(157, y, 375, y + 14, fill="#e9efeb", outline="")
            bar_width = max(2, int(218 * row["stock"] / max_stock))
            stock_canvas.create_rectangle(157, y, 157 + bar_width, y + 14, fill=GREEN if row["stock"] > 5 else AMBER, outline="")
            stock_canvas.create_text(394, y + 7, text=str(row["stock"]), anchor="e", fill=MUTED, font=("Segoe UI", 9, "bold"))

        trend_panel = self._panel(mid)
        trend_panel.pack(side="left", fill="both", expand=True, padx=(8, 0))
        tk.Label(trend_panel, text="Recent sales", font=("Segoe UI", 13, "bold"), fg=INK, bg=PANEL).pack(anchor="w")
        tk.Label(trend_panel, text="Daily sales from recorded orders", font=("Segoe UI", 9), fg=MUTED, bg=PANEL).pack(anchor="w", pady=(2, 8))
        chart = tk.Canvas(trend_panel, bg=PANEL, highlightthickness=0, height=240)
        chart.pack(fill="both", expand=True)
        trend = summary["trend"]
        max_sales = max((item["sales"] for item in trend), default=1) or 1
        if trend:
            for index, item in enumerate(trend):
                x = 34 + index * 63
                bar_height = max(5, int(140 * item["sales"] / max_sales))
                chart.create_rectangle(x, 175 - bar_height, x + 31, 175, fill=GREEN if index == len(trend) - 1 else "#9bc6ad", outline="")
                chart.create_text(x + 15, 188, text=item["day"][5:], fill=MUTED, font=("Segoe UI", 8))
                chart.create_text(x + 15, 165 - bar_height, text=f"{item['sales'] // 100:,}", fill=INK, font=("Segoe UI", 7))
        else:
            chart.create_text(170, 100, text="No sales recorded yet", fill=MUTED, font=("Segoe UI", 10))

        bottom = self._panel(parent, 15)
        bottom.pack(fill="both", expand=True)
        title_row = tk.Frame(bottom, bg=PANEL)
        title_row.pack(fill="x", pady=(0, 10))
        tk.Label(title_row, text="Latest orders", font=("Segoe UI", 12, "bold"), fg=INK, bg=PANEL).pack(side="left")
        ttk.Button(title_row, text="View orders", command=lambda: self.go("Orders"), style="Soft.TButton").pack(side="right")
        tree_host = ttk.Frame(bottom)
        tree_host.pack(fill="both", expand=True)
        tree = self._tree(tree_host, ("customer", "status", "items", "total", "date"), ("CUSTOMER", "STATUS", "ITEMS", "TOTAL", "DATE"), (240, 120, 80, 150, 170), height=4)
        for order in self.database.list_orders()[:5]:
            tree.insert("", "end", iid=order["id"], values=(order["customer_name"], order["status"].title(), order["item_count"], money(order["total_cents"]), order["created_at"][:16].replace("T", " ")))

    def render_checkout(self) -> None:
        parent = self._clear_content()
        self._page_heading(parent, "Checkout", "Build a basket, take payment, and print a receipt.")
        layout = ttk.Frame(parent)
        layout.pack(fill="both", expand=True)
        left = ttk.Frame(layout)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        right = ttk.Frame(layout, width=430)
        right.pack(side="left", fill="both", expand=True)
        right.pack_propagate(False)

        product_panel = self._panel(left, 14)
        product_panel.pack(fill="both", expand=True)
        tk.Label(product_panel, text="Choose products", font=("Segoe UI", 12, "bold"), fg=INK, bg=PANEL).pack(anchor="w", pady=(0, 9))
        search_row = ttk.Frame(product_panel)
        search_row.pack(fill="x", pady=(0, 9))
        search = ttk.Entry(search_row)
        search.pack(side="left", fill="x", expand=True)
        self.search_entry = search
        if self.user["role"] in ("admin", "manager"):
            ttk.Button(search_row, text="+ Add product", command=self.add_product_to_checkout, style="Soft.TButton").pack(side="right", padx=(8, 0))
        search.insert(0, "Search products")
        search.configure(foreground=MUTED)
        tree_host = ttk.Frame(product_panel)
        tree_host.pack(fill="both", expand=True)
        self.checkout_products = self._tree(tree_host, ("name", "stock", "price"), ("PRODUCT", "STOCK", "PRICE"), (260, 85, 130), height=15)
        self.checkout_products.bind("<Double-1>", lambda _event: self.add_selected_product())

        def refresh_products(_event: tk.Event[Any] | None = None) -> None:
            term = "" if search.get() == "Search products" else search.get()
            self.checkout_products.delete(*self.checkout_products.get_children())
            for product in self.database.list_products(term):
                if product["stock"] <= 0:
                    continue
                self.checkout_products.insert("", "end", iid=product["id"], values=(product["name"], product["stock"], money(product["price_cents"])))

        search.bind("<FocusIn>", lambda _event: search.delete(0, "end") if search.get() == "Search products" else None)
        search.bind("<KeyRelease>", refresh_products)
        refresh_products()
        ttk.Button(product_panel, text="Add selected item", command=self.add_selected_product, style="Soft.TButton").pack(anchor="e", pady=(9, 0))

        cart_panel = self._panel(right, 15)
        cart_panel.pack(fill="both", expand=True)
        cart_header = tk.Frame(cart_panel, bg=PANEL)
        cart_header.pack(fill="x", pady=(0, 9))
        tk.Label(cart_header, text="Current sale", font=("Segoe UI", 12, "bold"), fg=INK, bg=PANEL).pack(side="left")
        ttk.Button(cart_header, text="Remove item", command=self.remove_cart_item, style="Danger.TButton").pack(side="right")
        cart_host = ttk.Frame(cart_panel)
        cart_host.pack(fill="both", expand=True)
        self.cart_tree = self._tree(cart_host, ("product", "quantity", "price", "total"), ("PRODUCT", "QTY", "PRICE", "TOTAL"), (190, 55, 100, 110), height=11)
        self.cart_tree.bind("<Double-1>", lambda _event: self.change_cart_quantity())
        ttk.Button(cart_panel, text="Change quantity", command=self.change_cart_quantity, style="Soft.TButton").pack(anchor="e", pady=(6, 6))

        buyer_row = ttk.Frame(cart_panel)
        buyer_row.pack(fill="x", pady=(2, 9))
        ttk.Label(buyer_row, text="Customer").pack(side="left")
        self.customer_var = tk.StringVar()
        ttk.Entry(buyer_row, textvariable=self.customer_var).pack(side="right", fill="x", expand=True, padx=(12, 0))
        self.total_label = tk.Label(cart_panel, text="Total  Ksh 0.00", font=("Segoe UI", 17, "bold"), fg=INK, bg=PANEL)
        self.total_label.pack(anchor="e", pady=(4, 10))
        ttk.Button(cart_panel, text="Take payment", command=self.take_payment, style="Primary.TButton").pack(fill="x")
        ttk.Button(cart_panel, text="Save as pending", command=self.hold_current_order, style="Soft.TButton").pack(fill="x", pady=(7, 0))
        ttk.Button(cart_panel, text="Clear sale", command=self.clear_cart, style="Soft.TButton").pack(fill="x", pady=(7, 0))
        self.refresh_cart()

    def add_selected_product(self) -> None:
        selection = self.checkout_products.selection()
        if not selection:
            messagebox.showinfo("Choose a product", "Select a product first.")
            return
        product = next((item for item in self.database.list_products() if item["id"] == selection[0]), None)
        if not product:
            self.render_checkout()
            return
        current = self.cart.get(product["id"], 0)
        if current + 1 > product["stock"]:
            messagebox.showwarning("Stock limit", f"Only {product['stock']} units of {product['name']} are available.")
            return
        self.cart[product["id"]] = current + 1
        self.refresh_cart()

    def refresh_cart(self) -> None:
        if not hasattr(self, "cart_tree") or not self.cart_tree.winfo_exists():
            return
        self.cart_tree.delete(*self.cart_tree.get_children())
        products = {product["id"]: product for product in self.database.list_products()}
        subtotal = 0
        for product_id, quantity in self.cart.items():
            product = products.get(product_id)
            if not product:
                continue
            line_total = product["price_cents"] * quantity
            subtotal += line_total
            self.cart_tree.insert("", "end", iid=product_id, values=(product["name"], quantity, money(product["price_cents"]), money(line_total)))
        settings = self.database.get_settings()
        tax = (subtotal * int(settings["tax_rate_bps"]) + 5000) // 10000 if settings["tax_enabled"] == "1" else 0
        total = subtotal + tax
        tax_label = f"  incl. {int(settings['tax_rate_bps']) / 100:g}% VAT" if tax else "  VAT off"
        self.total_label.configure(text=f"Total  {money(total)}{tax_label}")

    def remove_cart_item(self) -> None:
        selection = self.cart_tree.selection()
        if selection:
            self.cart.pop(selection[0], None)
            self.refresh_cart()

    def change_cart_quantity(self) -> None:
        selection = self.cart_tree.selection()
        if not selection:
            return
        product_id = selection[0]
        current = self.cart[product_id]
        dialog = QuantityDialog(self.root, current)
        self.root.wait_window(dialog)
        if dialog.result is None:
            return
        product = next((item for item in self.database.list_products() if item["id"] == product_id), None)
        if not product or dialog.result > product["stock"]:
            messagebox.showwarning("Stock limit", f"Only {product['stock'] if product else 0} units are available.")
            return
        self.cart[product_id] = dialog.result
        self.refresh_cart()

    def clear_cart(self) -> None:
        if self.cart and messagebox.askyesno("Clear sale", "Remove all items from this sale?"):
            self.cart.clear()
            self.customer_var.set("")
            self.refresh_cart()

    def take_payment(self) -> None:
        if not self.cart:
            messagebox.showinfo("Empty sale", "Add products before taking payment.")
            return
        settings = self.database.get_settings()
        subtotal = sum(
            product["price_cents"] * quantity
            for product in self.database.list_products()
            for product_id, quantity in self.cart.items()
            if product["id"] == product_id
        )
        rate = int(settings["tax_rate_bps"]) if settings["tax_enabled"] == "1" else 0
        total = subtotal + (subtotal * rate + 5000) // 10000
        dialog = PaymentDialog(self.root, total)
        self.root.wait_window(dialog)
        if not dialog.result:
            return
        try:
            order_id = self.database.create_order(
                self.customer_var.get(), self.cart, dialog.result["method"],
                dialog.result["received_cents"], rate,
            )
        except PosError as error:
            messagebox.showerror("Could not complete sale", str(error))
            self.render_checkout()
            return
        self.cart.clear()
        self.customer_var.set("")
        self.selected_order_id = order_id
        self.show_pending_only = False
        self.go("Orders")
        messagebox.showinfo("Sale complete", "Payment saved and stock updated.")
        self.show_receipt(order_id)

    def hold_current_order(self) -> None:
        if not self.cart:
            messagebox.showinfo("Empty sale", "Add products before saving a pending order.")
            return
        settings = self.database.get_settings()
        rate = int(settings["tax_rate_bps"]) if settings["tax_enabled"] == "1" else 0
        try:
            order_id = self.database.create_order(
                self.customer_var.get(), self.cart, "Pending", 0, rate, pending=True,
            )
        except PosError as error:
            messagebox.showerror("Order not saved", str(error))
            self.render_checkout()
            return
        self.cart.clear()
        self.customer_var.set("")
        self.selected_order_id = order_id
        self.show_pending_only = True
        self.go("Orders")
        messagebox.showinfo("Order saved", "Order held for payment. Its items are reserved from stock.")

    def add_product_to_checkout(self) -> None:
        if not self.user or self.user["role"] not in ("admin", "manager"):
            return
        dialog = ProductDialog(self.root, None)
        self.root.wait_window(dialog)
        if not dialog.result:
            return
        try:
            product_id = self.database.save_product(**dialog.result)
        except PosError as error:
            messagebox.showerror("Product not saved", str(error))
            return
        if dialog.result["stock"] > 0:
            self.cart[product_id] = self.cart.get(product_id, 0) + 1
        self.render_checkout()

    def render_products(self) -> None:
        parent = self._clear_content()
        can_manage = self.user["role"] in ("admin", "manager")
        self._page_heading(parent, "Products", "Catalog, pricing, and on-hand inventory.", ("Add product", self.add_product) if can_manage else None)
        controls = ttk.Frame(parent)
        controls.pack(fill="x", pady=(0, 10))
        search = ttk.Entry(controls, width=36)
        search.pack(side="left")
        self.search_entry = search
        search.insert(0, "Search name or category")
        host = self._panel(parent, 12)
        host.pack(fill="both", expand=True)
        tree_host = ttk.Frame(host)
        tree_host.pack(fill="both", expand=True)
        tree = self._tree(tree_host, ("name", "category", "price", "stock", "updated"), ("PRODUCT", "CATEGORY", "PRICE", "IN STOCK", "UPDATED"), (260, 170, 140, 110, 190), height=15)

        def refresh(_event: tk.Event[Any] | None = None) -> None:
            term = "" if search.get() == "Search name or category" else search.get()
            tree.delete(*tree.get_children())
            for product in self.database.list_products(term):
                tree.insert("", "end", iid=product["id"], values=(product["name"], product["category"], money(product["price_cents"]), product["stock"], product["updated_at"][:10]))

        search.bind("<FocusIn>", lambda _event: search.delete(0, "end") if search.get() == "Search name or category" else None)
        search.bind("<KeyRelease>", refresh)
        refresh()
        if can_manage:
            actions = ttk.Frame(parent)
            actions.pack(fill="x", pady=(10, 0))
            ttk.Button(actions, text="Edit selected", command=lambda: self.edit_product(tree), style="Soft.TButton").pack(side="left")
            ttk.Button(actions, text="Delete selected", command=lambda: self.delete_product(tree), style="Danger.TButton").pack(side="left", padx=8)
        tree.bind("<Double-1>", lambda _event: self.edit_product(tree) if can_manage else None)

    def edit_product(self, tree: ttk.Treeview | None = None) -> None:
        product = None
        if tree and tree.selection():
            product_id = tree.selection()[0]
            product = next((item for item in self.database.list_products() if item["id"] == product_id), None)
        dialog = ProductDialog(self.root, product)
        self.root.wait_window(dialog)
        if not dialog.result:
            return
        try:
            self.database.save_product(**dialog.result)
        except PosError as error:
            messagebox.showerror("Product not saved", str(error))
            return
        self.render_products()

    def add_product(self) -> None:
        if not self.user or self.user["role"] not in ("admin", "manager"):
            return
        dialog = ProductDialog(self.root, None)
        self.root.wait_window(dialog)
        if not dialog.result:
            return
        try:
            self.database.save_product(**dialog.result)
        except PosError as error:
            messagebox.showerror("Product not saved", str(error))
            return
        self.show_main()

    def delete_product(self, tree: ttk.Treeview) -> None:
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Choose a product", "Select a product to delete.")
            return
        if not messagebox.askyesno("Delete product", "Delete the selected product? Products in past sales cannot be removed."):
            return
        try:
            self.database.delete_product(selection[0])
        except PosError as error:
            messagebox.showerror("Product not deleted", str(error))
            return
        self.render_products()

    def render_orders(self) -> None:
        parent = self._clear_content()
        self._page_heading(parent, "Orders", "Create sales, review pending payments, and print receipts.", ("+ New order", self.start_new_order))
        controls = ttk.Frame(parent)
        controls.pack(fill="x", pady=(0, 11))
        search = ttk.Entry(controls, width=38)
        search.pack(side="left")
        self.search_entry = search
        search.insert(0, "Search customer, order, status")
        pending_filter = tk.BooleanVar(value=self.show_pending_only)
        layout = ttk.Frame(parent)
        layout.pack(fill="both", expand=True)
        left = self._panel(layout, 12)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        right = self._panel(layout, 18)
        right.pack(side="left", fill="y")
        tree_host = ttk.Frame(left)
        tree_host.pack(fill="both", expand=True)
        tree = self._tree(tree_host, ("customer", "status", "items", "total", "date"), ("CUSTOMER", "STATUS", "ITEMS", "TOTAL", "DATE"), (185, 100, 65, 130, 145), height=17)
        self.order_tree = tree
        summary = tk.Frame(right, bg=PANEL, width=340)
        summary.pack(fill="both", expand=True)
        summary.pack_propagate(False)
        tk.Label(summary, text="Sale details", font=("Segoe UI", 13, "bold"), fg=INK, bg=PANEL).pack(anchor="w")
        self.order_detail_text = tk.Text(summary, height=13, width=37, wrap="word", relief="flat", bg="#f6f8f5", fg=INK, font=("Segoe UI", 9), padx=10, pady=10)
        self.order_detail_text.pack(fill="both", expand=True, pady=(10, 12))
        status_row = ttk.Frame(summary)
        status_row.pack(fill="x", pady=(0, 9))
        ttk.Label(status_row, text="Status").pack(side="left")
        self.order_status_var = tk.StringVar(value="paid")
        self.order_status_select = ttk.Combobox(status_row, textvariable=self.order_status_var, values=("pending", "paid", "completed", "cancelled"), state="readonly", width=13)
        self.order_status_select.pack(side="right")
        self.order_status_select.configure(state="readonly" if self.user["role"] in ("admin", "manager") else "disabled")
        buttons = ttk.Frame(summary)
        buttons.pack(fill="x")
        if self.user["role"] in ("admin", "manager"):
            ttk.Button(buttons, text="Update status", command=self.change_selected_order_status, style="Soft.TButton").pack(side="left")
        ttk.Button(buttons, text="Receipt", command=lambda: self.show_receipt(self.selected_order_id) if self.selected_order_id else None, style="Primary.TButton").pack(side="right")

        def refresh(_event: tk.Event[Any] | None = None) -> None:
            term = "" if search.get() == "Search customer, order, status" else search.get()
            tree.delete(*tree.get_children())
            orders = self.database.list_orders(term)
            if pending_filter.get():
                orders = [order for order in orders if order["status"] == "pending"]
            for order in orders:
                tree.insert("", "end", iid=order["id"], values=(order["customer_name"], order["status"].title(), order["item_count"], money(order["total_cents"]), order["created_at"][:16].replace("T", " ")))
            if self.selected_order_id and tree.exists(self.selected_order_id):
                tree.selection_set(self.selected_order_id)
                self._show_order_detail(self.selected_order_id)
            elif orders:
                tree.selection_set(orders[0]["id"])
                self._show_order_detail(orders[0]["id"])
            else:
                self.selected_order_id = None
                self._show_order_detail(None)

        search.bind("<FocusIn>", lambda _event: search.delete(0, "end") if search.get() == "Search customer, order, status" else None)
        search.bind("<KeyRelease>", refresh)
        ttk.Checkbutton(
            controls,
            text="Pending only",
            variable=pending_filter,
            command=lambda: (setattr(self, "show_pending_only", pending_filter.get()), refresh()),
        ).pack(side="left", padx=12)
        tree.bind("<<TreeviewSelect>>", lambda _event: self._show_order_detail(tree.selection()[0]) if tree.selection() else None)
        refresh()

    def _show_order_detail(self, order_id: str | None) -> None:
        if not hasattr(self, "order_detail_text") or not self.order_detail_text.winfo_exists():
            return
        order = self.database.get_order(order_id) if order_id else None
        self.order_detail_text.configure(state="normal")
        self.order_detail_text.delete("1.0", "end")
        if not order:
            self.order_detail_text.insert("1.0", "Select an order to see its items and payment details.")
            self.order_status_var.set("paid")
            self.selected_order_id = None
        else:
            self.selected_order_id = order["id"]
            self.order_status_var.set(order["status"])
            lines = [
                f"{order['customer_name']}\n{order['created_at'][:19].replace('T', ' ')}\n",
                "ITEMS",
            ]
            lines.extend(f"{item['quantity']} x {item['product_name']}    {money(item['subtotal_cents'])}" for item in order["items"])
            lines.extend(("", f"Subtotal          {money(order['subtotal_cents'])}", f"VAT               {money(order['tax_cents'])}", f"TOTAL             {money(order['total_cents'])}", f"Payment           {order['payment_method']}", f"Received          {money(order['amount_received_cents'])}", f"Change            {money(order['change_cents'])}"))
            self.order_detail_text.insert("1.0", "\n".join(lines))
        self.order_detail_text.configure(state="disabled")

    def change_selected_order_status(self) -> None:
        if not self.selected_order_id:
            return
        status = self.order_status_var.get()
        if status == "cancelled" and not messagebox.askyesno("Cancel sale", "Cancel this order and return its quantities to inventory?"):
            return
        order = self.database.get_order(self.selected_order_id)
        if not order:
            return
        try:
            if order["status"] in ("pending", "cancelled") and status in ("paid", "completed"):
                dialog = PaymentDialog(self.root, order["total_cents"])
                self.root.wait_window(dialog)
                if not dialog.result:
                    return
                self.database.record_order_payment(
                    self.selected_order_id, dialog.result["method"], dialog.result["received_cents"],
                )
                if status == "completed":
                    self.database.update_order_status(self.selected_order_id, "completed")
            else:
                self.database.update_order_status(self.selected_order_id, status)
        except PosError as error:
            messagebox.showerror("Status not updated", str(error))
            return
        self.show_main()

    def show_receipt(self, order_id: str) -> None:
        order = self.database.get_order(order_id)
        if not order:
            messagebox.showerror("Receipt unavailable", "This order could not be found.")
            return
        settings = self.database.get_settings()
        lines = [
            settings["store_name"],
            "SALES RECEIPT",
            "=" * 38,
            f"Order: {order['id']}",
            f"Date: {order['created_at'][:19].replace('T', ' ')}",
            f"Customer: {order['customer_name']}",
            "-" * 38,
        ]
        for item in order["items"]:
            lines.append(f"{item['product_name'][:21]}")
            lines.append(f"  {item['quantity']} x {money(item['unit_price_cents'])} = {money(item['subtotal_cents'])}")
        lines.extend(("-" * 38, f"Subtotal: {money(order['subtotal_cents'])}", f"VAT: {money(order['tax_cents'])}", f"TOTAL: {money(order['total_cents'])}", f"Payment: {order['payment_method']}", f"Received: {money(order['amount_received_cents'])}", f"Change: {money(order['change_cents'])}", "=" * 38, "Thank you for shopping with us."))
        receipt = "\n".join(lines)
        receipt_dir = DATA_DIR / "receipts"
        receipt_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = receipt_dir / f"receipt-{order_id[:8]}.txt"
        receipt_path.write_text(receipt + "\n", encoding="utf-8")

        window = tk.Toplevel(self.root)
        window.title("Receipt")
        window.transient(self.root)
        window.geometry("430x600")
        body = ttk.Frame(window, padding=16)
        body.pack(fill="both", expand=True)
        text = tk.Text(body, wrap="none", font=("Consolas", 10), bg="white", fg=INK, padx=14, pady=14)
        text.pack(fill="both", expand=True)
        text.insert("1.0", receipt)
        text.configure(state="disabled")
        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Print receipt", command=lambda: self.print_receipt(receipt_path), style="Primary.TButton").pack(side="left")
        ttk.Button(buttons, text="Close", command=window.destroy, style="Soft.TButton").pack(side="right")

    def print_receipt(self, receipt_path: Path) -> None:
        try:
            os.startfile(str(receipt_path), "print")
        except (AttributeError, OSError) as error:
            messagebox.showinfo("Receipt saved", f"Receipt file saved at:\n{receipt_path}\n\nAutomatic printing is not available on this computer.\n{error}")

    def render_reports(self) -> None:
        parent = self._clear_content()
        self._page_heading(parent, "Reports", "Filter recorded sales by date and export a CSV report.")
        controls = ttk.Frame(parent)
        controls.pack(fill="x", pady=(0, 12))
        ttk.Label(controls, text="From (YYYY-MM-DD)").pack(side="left")
        start_var = tk.StringVar(value=date.today().replace(day=1).isoformat())
        start = ttk.Entry(controls, textvariable=start_var, width=14)
        start.pack(side="left", padx=(7, 16))
        ttk.Label(controls, text="To").pack(side="left")
        end_var = tk.StringVar(value=date.today().isoformat())
        end = ttk.Entry(controls, textvariable=end_var, width=14)
        end.pack(side="left", padx=(7, 12))
        rows_frame = self._panel(parent, 13)
        rows_frame.pack(fill="both", expand=True)
        host = ttk.Frame(rows_frame)
        host.pack(fill="both", expand=True)
        tree = self._tree(host, ("customer", "status", "payment", "items", "total", "date"), ("CUSTOMER", "STATUS", "PAYMENT", "ITEMS", "TOTAL", "DATE"), (195, 100, 110, 70, 140, 165), height=15)
        summary = tk.StringVar()
        ttk.Label(parent, textvariable=summary, style="Section.TLabel").pack(anchor="w", pady=(12, 0))
        current_report: list[dict[str, Any]] = []

        def report_rows() -> list[dict[str, Any]]:
            try:
                start_date = date.fromisoformat(start_var.get().strip())
                end_date = date.fromisoformat(end_var.get().strip())
            except ValueError:
                raise PosError("Dates must use YYYY-MM-DD format.") from None
            if end_date < start_date:
                raise PosError("The end date must be on or after the start date.")
            return [order for order in self.database.list_orders() if start_var.get() <= order["created_at"][:10] <= end_var.get()]

        def refresh() -> None:
            try:
                current_report[:] = report_rows()
            except PosError as error:
                messagebox.showerror("Invalid date range", str(error))
                return
            tree.delete(*tree.get_children())
            for order in current_report:
                tree.insert("", "end", iid=order["id"], values=(order["customer_name"], order["status"].title(), order["payment_method"], order["item_count"], money(order["total_cents"]), order["created_at"][:10]))
            total_sales = sum(order["total_cents"] for order in current_report if order["status"] in ("paid", "completed"))
            summary.set(f"{len(current_report)} orders     Paid sales: {money(total_sales)}")

        def export() -> None:
            try:
                rows = report_rows()
            except PosError as error:
                messagebox.showerror("Invalid date range", str(error))
                return
            if not rows:
                messagebox.showinfo("Nothing to export", "There are no orders in this date range.")
                return
            path = filedialog.asksaveasfilename(
                parent=self.root, title="Save sales report", defaultextension=".csv",
                initialfile="stevo-sales-report.csv", filetypes=(("CSV file", "*.csv"),),
            )
            if not path:
                return
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(("Order ID", "Customer", "Total Ksh", "VAT Ksh", "Status", "Payment", "Created", "Items"))
                for order in rows:
                    writer.writerow((order["id"], order["customer_name"], f"{Decimal(order['total_cents']) / 100:.2f}", f"{Decimal(order['tax_cents']) / 100:.2f}", order["status"], order["payment_method"], order["created_at"], order["item_count"]))
            messagebox.showinfo("Report exported", f"Saved {len(rows)} orders to:\n{path}")

        ttk.Button(controls, text="Apply dates", command=refresh, style="Soft.TButton").pack(side="left")
        ttk.Button(controls, text="Export CSV", command=export, style="Primary.TButton").pack(side="right")
        refresh()

    def render_settings(self) -> None:
        parent = self._clear_content()
        self._page_heading(parent, "Settings", "Store identity and local sales tax.")
        settings = self.database.get_settings()
        panel = self._panel(parent, 24)
        panel.pack(fill="x", anchor="n")
        tk.Label(panel, text="Store name", font=("Segoe UI", 12, "bold"), fg=INK, bg=PANEL).grid(row=0, column=0, sticky="w")
        tk.Label(panel, text="Printed at the top of receipts", font=("Segoe UI", 9), fg=MUTED, bg=PANEL).grid(row=1, column=0, sticky="w", pady=(3, 0))
        store_name = tk.StringVar(value=settings["store_name"])
        ttk.Entry(panel, textvariable=store_name, width=42).grid(row=2, column=0, sticky="w", pady=(12, 4))
        tk.Frame(panel, bg=LINE, height=1).grid(row=3, column=0, sticky="ew", pady=17)
        tax_enabled = tk.BooleanVar(value=settings["tax_enabled"] == "1")
        ttk.Checkbutton(panel, text="Apply VAT to new sales", variable=tax_enabled).grid(row=4, column=0, sticky="w")
        tk.Label(panel, text="Tax rate (%)", font=("Segoe UI", 9, "bold"), fg=MUTED, bg=PANEL).grid(row=5, column=0, sticky="w", pady=(12, 3))
        tax_rate = tk.StringVar(value=f"{int(settings['tax_rate_bps']) / 100:g}")
        ttk.Entry(panel, textvariable=tax_rate, width=12).grid(row=6, column=0, sticky="w")

        def save() -> None:
            name = store_name.get().strip()
            if not name:
                messagebox.showerror("Invalid store name", "Store name cannot be empty.")
                return
            try:
                rate = Decimal(tax_rate.get().strip())
                if not rate.is_finite() or rate < 0 or rate > 100:
                    raise InvalidOperation
                basis_points = int((rate * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            except (InvalidOperation, ValueError):
                messagebox.showerror("Invalid tax rate", "Enter a tax rate from 0 to 100%.")
                return
            self.database.set_setting("store_name", name)
            self.database.set_setting("tax_enabled", "1" if tax_enabled.get() else "0")
            self.database.set_setting("tax_rate_bps", str(basis_points))
            messagebox.showinfo("Settings saved", "Your store settings have been saved on this computer.")
            self.show_main()

        ttk.Button(panel, text="Save settings", command=save, style="Primary.TButton").grid(row=7, column=0, sticky="w", pady=(20, 0))
        panel.columnconfigure(0, weight=1)

    def render_users(self) -> None:
        parent = self._clear_content()
        self._page_heading(parent, "Users", "Create staff logins and manage their access.", ("Add user", self.add_user))
        panel = self._panel(parent, 13)
        panel.pack(fill="both", expand=True)
        host = ttk.Frame(panel)
        host.pack(fill="both", expand=True)
        tree = self._tree(host, ("username", "role", "created"), ("USERNAME", "ROLE", "CREATED"), (280, 180, 220), height=15)
        for user in self.database.list_users():
            tree.insert("", "end", iid=user["id"], values=(user["username"], user["role"].title(), user["created_at"][:10]))
        actions = ttk.Frame(parent)
        actions.pack(fill="x", pady=(10, 0))
        ttk.Button(actions, text="Remove selected user", command=lambda: self.delete_user(tree), style="Danger.TButton").pack(side="left")

    def add_user(self) -> None:
        dialog = UserDialog(self.root)
        self.root.wait_window(dialog)
        if not dialog.result:
            return
        try:
            self.database.add_user(**dialog.result)
        except PosError as error:
            messagebox.showerror("User not created", str(error))
            return
        self.render_users()

    def delete_user(self, tree: ttk.Treeview) -> None:
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Choose a user", "Select a user to remove.")
            return
        if selection[0] == self.user["id"]:
            messagebox.showerror("Cannot remove yourself", "Sign in as another administrator to remove this account.")
            return
        if not messagebox.askyesno("Remove user", "Remove the selected login?"):
            return
        try:
            self.database.delete_user(selection[0])
        except PosError as error:
            messagebox.showerror("User not removed", str(error))
            return
        self.render_users()


class Modal(tk.Toplevel):
    def __init__(self, parent: tk.Misc, title: str, size: str):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.resizable(False, False)
        self.geometry(size)
        self.configure(background=BG)
        self.result: Any = None
        self.bind("<Escape>", lambda _event: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def body(self, title: str, subtitle: str = "") -> ttk.Frame:
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=title, style="Section.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(frame, text=subtitle, style="Muted.TLabel").pack(anchor="w", pady=(3, 13))
        return frame


class ProductDialog(Modal):
    def __init__(self, parent: tk.Misc, product: dict[str, Any] | None):
        super().__init__(parent, "Edit product" if product else "Add product", "440x440")
        self.product = product
        frame = self.body("Product details", "Prices are entered in Kenyan shillings.")
        self.name = tk.StringVar(value=product["name"] if product else "")
        self.category = tk.StringVar(value=product["category"] if product else "General")
        self.price = tk.StringVar(value=f"{Decimal(product['price_cents']) / 100:.2f}" if product else "")
        self.stock = tk.StringVar(value=str(product["stock"]) if product else "0")
        self._field(frame, "Product name", self.name)
        self._field(frame, "Category", self.category)
        self._field(frame, "Unit price", self.price)
        self._field(frame, "Opening stock", self.stock)
        ttk.Button(frame, text="Save product", command=self.save, style="Primary.TButton").pack(fill="x", pady=(15, 0))

    @staticmethod
    def _field(parent: ttk.Frame, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label, style="Muted.TLabel").pack(anchor="w", pady=(7, 3))
        ttk.Entry(parent, textvariable=variable).pack(fill="x")

    def save(self) -> None:
        try:
            stock = int(self.stock.get())
            if stock < 0:
                raise ValueError
            self.result = {
                "name": self.name.get(),
                "category": self.category.get(),
                "price_cents": parse_cents(self.price.get()),
                "stock": stock,
                "product_id": self.product["id"] if self.product else None,
            }
        except (ValueError, PosError):
            messagebox.showerror("Invalid product", "Enter a valid non-negative price and whole-number stock quantity.", parent=self)
            return
        self.destroy()


class UserDialog(Modal):
    def __init__(self, parent: tk.Misc):
        super().__init__(parent, "Add user", "400x400")
        frame = self.body("Create staff login", "Passwords are stored as one-way salted hashes.")
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.role = tk.StringVar(value="cashier")
        ProductDialog._field(frame, "Username", self.username)
        ProductDialog._field(frame, "Password (at least 6 characters)", self.password)
        self.password_entry = frame.winfo_children()[-1]
        self.password_entry.configure(show="•")
        ttk.Label(frame, text="Role", style="Muted.TLabel").pack(anchor="w", pady=(7, 3))
        ttk.Combobox(frame, textvariable=self.role, values=("cashier", "manager", "admin"), state="readonly").pack(fill="x")
        ttk.Button(frame, text="Create account", command=self.save, style="Primary.TButton").pack(fill="x", pady=(17, 0))

    def save(self) -> None:
        self.result = {"username": self.username.get(), "password": self.password.get(), "role": self.role.get()}
        self.destroy()


class QuantityDialog(Modal):
    def __init__(self, parent: tk.Misc, quantity: int):
        super().__init__(parent, "Change quantity", "330x210")
        frame = self.body("Item quantity")
        self.quantity = tk.StringVar(value=str(quantity))
        ttk.Entry(frame, textvariable=self.quantity).pack(fill="x", pady=(8, 12))
        ttk.Button(frame, text="Update quantity", command=self.save, style="Primary.TButton").pack(fill="x")

    def save(self) -> None:
        try:
            value = int(self.quantity.get())
            if value < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid quantity", "Enter a whole number greater than zero.", parent=self)
            return
        self.result = value
        self.destroy()


class PaymentDialog(Modal):
    def __init__(self, parent: tk.Misc, total_cents: int):
        super().__init__(parent, "Take payment", "430x410")
        self.total_cents = total_cents
        frame = self.body("Take payment", f"Amount due  {money(total_cents)}")
        self.method = tk.StringVar(value="Cash")
        self.received = tk.StringVar(value=f"{Decimal(total_cents) / 100:.2f}")
        ttk.Label(frame, text="Payment method", style="Muted.TLabel").pack(anchor="w", pady=(5, 3))
        method = ttk.Combobox(frame, textvariable=self.method, values=("Cash", "M-Pesa", "Card"), state="readonly")
        method.pack(fill="x")
        ttk.Label(frame, text="Amount received (Ksh)", style="Muted.TLabel").pack(anchor="w", pady=(12, 3))
        self.received_entry = ttk.Entry(frame, textvariable=self.received)
        self.received_entry.pack(fill="x")
        self.change_label = ttk.Label(frame, text="Change due  Ksh 0.00", style="Section.TLabel")
        self.change_label.pack(anchor="w", pady=(14, 12))
        method.bind("<<ComboboxSelected>>", lambda _event: self._payment_method_changed())
        self.received.trace_add("write", lambda *_args: self._update_change())
        self._payment_method_changed()
        ttk.Button(frame, text="Complete sale", command=self.save, style="Primary.TButton").pack(fill="x", pady=(3, 0))

    def _payment_method_changed(self) -> None:
        if self.method.get() == "Cash":
            self.received_entry.configure(state="normal")
            self.received_entry.focus_set()
        else:
            self.received.set(f"{Decimal(self.total_cents) / 100:.2f}")
            self.received_entry.configure(state="disabled")
        self._update_change()

    def _update_change(self) -> None:
        try:
            received = parse_cents(self.received.get())
            change = max(0, received - self.total_cents) if self.method.get() == "Cash" else 0
            self.change_label.configure(text=f"Change due  {money(change)}")
        except PosError:
            self.change_label.configure(text="Enter a valid received amount")

    def save(self) -> None:
        try:
            received_cents = parse_cents(self.received.get()) if self.method.get() == "Cash" else self.total_cents
            if received_cents < self.total_cents:
                raise PosError("Amount received is less than the total due.")
        except PosError as error:
            messagebox.showerror("Payment not complete", str(error), parent=self)
            return
        self.result = {"method": self.method.get(), "received_cents": received_cents}
        self.destroy()


class OrderEntryDialog(Modal):
    def __init__(self, parent: tk.Misc, database: PosDatabase, role: str):
        super().__init__(parent, "New order", "760x690")
        self.database = database
        self.role = role
        self.items: dict[str, int] = {}
        self.products_by_label: dict[str, dict[str, Any]] = {}
        settings = self.database.get_settings()
        self.tax_rate_bps = int(settings["tax_rate_bps"]) if settings["tax_enabled"] == "1" else 0
        frame = self.body("Create order", "Add products and choose whether to record payment now or save it pending.")

        ttk.Label(frame, text="Customer name (optional)", style="Muted.TLabel").pack(anchor="w")
        self.customer = tk.StringVar()
        ttk.Entry(frame, textvariable=self.customer).pack(fill="x", pady=(4, 14))

        picker = ttk.Frame(frame)
        picker.pack(fill="x")
        ttk.Label(picker, text="Product", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(picker, text="Quantity", style="Muted.TLabel").grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.product_var = tk.StringVar()
        self.product_select = ttk.Combobox(picker, textvariable=self.product_var, state="readonly", width=45)
        self.product_select.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.quantity_var = tk.StringVar(value="1")
        ttk.Spinbox(picker, textvariable=self.quantity_var, from_=1, to=9999, width=7).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
        ttk.Button(picker, text="Add item", command=self.add_item, style="Primary.TButton").grid(row=1, column=2, padx=(8, 0), pady=(4, 0))
        if role in ("admin", "manager"):
            ttk.Button(picker, text="+ New product", command=self.add_product, style="Soft.TButton").grid(row=1, column=3, padx=(8, 0), pady=(4, 0))
        picker.columnconfigure(0, weight=1)

        table_panel = self._panel(frame, 8)
        table_panel.pack(fill="both", expand=True, pady=(15, 10))
        host = ttk.Frame(table_panel)
        host.pack(fill="both", expand=True)
        self.items_tree = ttk.Treeview(
            host, columns=("product", "quantity", "unit", "total"), show="headings", height=10,
        )
        for column, heading, width in (
            ("product", "PRODUCT", 285), ("quantity", "QTY", 70),
            ("unit", "UNIT PRICE", 130), ("total", "LINE TOTAL", 140),
        ):
            self.items_tree.heading(column, text=heading)
            self.items_tree.column(column, width=width, anchor="w" if column == "product" else "center")
        self.items_tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(host, orient="vertical", command=self.items_tree.yview)
        scroll.pack(side="right", fill="y")
        self.items_tree.configure(yscrollcommand=scroll.set)
        ttk.Button(frame, text="Remove selected item", command=self.remove_item, style="Danger.TButton").pack(anchor="e")

        self.total_text = tk.StringVar()
        ttk.Label(frame, textvariable=self.total_text, style="Section.TLabel").pack(anchor="e", pady=(12, 8))
        actions = ttk.Frame(frame)
        actions.pack(fill="x")
        ttk.Button(actions, text="Save pending", command=lambda: self.save_order(pending=True), style="Soft.TButton").pack(side="left")
        ttk.Button(actions, text="Take payment", command=lambda: self.save_order(pending=False), style="Primary.TButton").pack(side="right")
        self.refresh_products()
        self.refresh_items()

    def _panel(self, parent: tk.Misc, padding: int) -> tk.Frame:
        return tk.Frame(parent, bg=PANEL, padx=padding, pady=padding, highlightthickness=1, highlightbackground=LINE)

    def refresh_products(self) -> None:
        self.products_by_label.clear()
        labels = []
        for product in self.database.list_products():
            available = product["stock"] - self.items.get(product["id"], 0)
            if available <= 0:
                continue
            label = f"{product['name']} ({available} available) | {money(product['price_cents'])} [{product['id'][:6]}]"
            self.products_by_label[label] = product
            labels.append(label)
        self.product_select.configure(values=labels)
        if self.product_var.get() not in self.products_by_label:
            self.product_var.set(labels[0] if labels else "")

    def add_item(self) -> None:
        product = self.products_by_label.get(self.product_var.get())
        if not product:
            messagebox.showinfo("No products available", "Add a product with stock before creating an order.", parent=self)
            return
        try:
            quantity = int(self.quantity_var.get())
            if quantity < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid quantity", "Quantity must be a whole number greater than zero.", parent=self)
            return
        current_quantity = self.items.get(product["id"], 0)
        if current_quantity + quantity > product["stock"]:
            messagebox.showerror(
                "Not enough stock",
                f"Only {product['stock'] - current_quantity} more units of {product['name']} are available.",
                parent=self,
            )
            return
        self.items[product["id"]] = current_quantity + quantity
        self.quantity_var.set("1")
        self.refresh_items()

    def remove_item(self) -> None:
        selection = self.items_tree.selection()
        if selection:
            self.items.pop(selection[0], None)
            self.refresh_items()

    def refresh_items(self) -> None:
        self.items_tree.delete(*self.items_tree.get_children())
        products = {product["id"]: product for product in self.database.list_products()}
        subtotal = 0
        for product_id, quantity in self.items.items():
            product = products.get(product_id)
            if not product:
                continue
            line_total = product["price_cents"] * quantity
            subtotal += line_total
            self.items_tree.insert(
                "", "end", iid=product_id,
                values=(product["name"], quantity, money(product["price_cents"]), money(line_total)),
            )
        tax = (subtotal * self.tax_rate_bps + 5000) // 10000
        self.total_text.set(f"Subtotal  {money(subtotal)}     VAT  {money(tax)}     Total  {money(subtotal + tax)}")
        self.refresh_products()

    def add_product(self) -> None:
        dialog = ProductDialog(self, None)
        self.wait_window(dialog)
        if not dialog.result:
            return
        try:
            self.database.save_product(**dialog.result)
        except PosError as error:
            messagebox.showerror("Product not saved", str(error), parent=self)
            return
        self.refresh_products()

    def save_order(self, pending: bool) -> None:
        if not self.items:
            messagebox.showinfo("Order is empty", "Add at least one product before saving the order.", parent=self)
            return
        products = {product["id"]: product for product in self.database.list_products()}
        subtotal = sum(products[product_id]["price_cents"] * quantity for product_id, quantity in self.items.items())
        total = subtotal + (subtotal * self.tax_rate_bps + 5000) // 10000
        payment_method = "Pending"
        amount_received = 0
        if not pending:
            payment = PaymentDialog(self, total)
            self.wait_window(payment)
            if not payment.result:
                return
            payment_method = payment.result["method"]
            amount_received = payment.result["received_cents"]
        try:
            order_id = self.database.create_order(
                self.customer.get(), self.items, payment_method, amount_received,
                self.tax_rate_bps, pending=pending,
            )
        except PosError as error:
            messagebox.showerror("Order not saved", str(error), parent=self)
            self.refresh_products()
            return
        self.result = {"order_id": order_id, "status": "pending" if pending else "paid"}
        self.destroy()


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    database = PosDatabase(DATABASE_PATH)
    root = tk.Tk()
    OfflinePos(root, database)
    root.mainloop()


if __name__ == "__main__":
    main()