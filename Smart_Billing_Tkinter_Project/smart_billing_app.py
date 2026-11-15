"""
Smart Billing & Discount Calculator — Tkinter edition.

Run: python smart_billing_app.py
Standard-library only.
"""
from __future__ import annotations

import csv
import json
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

APP_DIR = Path(__file__).resolve().parent
HISTORY_FILE = APP_DIR / "bill_history.json"
CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def parse_decimal(value: str, field_name: str) -> Decimal:
    try:
        result = Decimal(value.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError(f"{field_name} must be a valid number.")
    if not result.is_finite():
        raise ValueError(f"{field_name} must be a finite number.")
    return result


@dataclass
class CartItem:
    description: str
    category: str
    unit_price: Decimal
    quantity: int

    @property
    def line_total(self) -> Decimal:
        return money(self.unit_price * self.quantity)


def validate_item(description: str, category: str, unit_price: Decimal, quantity: int) -> None:
    if not description.strip():
        raise ValueError("Product description cannot be empty.")
    if not category.strip():
        raise ValueError("Please select a product category.")
    if unit_price < 0:
        raise ValueError("Unit price cannot be negative.")
    if quantity <= 0:
        raise ValueError("Quantity must be a positive whole number.")


def calculate_bill(items: list[CartItem], discount_type: str = "None",
                   discount_value: Decimal = Decimal("0")) -> dict:
    subtotal = money(sum((item.line_total for item in items), Decimal("0")))
    if discount_value < 0:
        raise ValueError("Discount cannot be negative.")

    if discount_type == "Percentage":
        if discount_value > 100:
            raise ValueError("Percentage discount cannot exceed 100%.")
        raw_discount = subtotal * discount_value / Decimal("100")
        note = f"{discount_value}% discount applied to the bill subtotal."
    elif discount_type == "Fixed Amount":
        raw_discount = discount_value
        note = f"Fixed discount of ₹ {money(discount_value):.2f} applied."
    elif discount_type == "None":
        raw_discount = Decimal("0")
        note = "No discount applied."
    else:
        raise ValueError("Choose a valid discount type.")

    # A discount can never exceed the bill subtotal.
    discount = money(min(max(raw_discount, Decimal("0")), subtotal))
    net_payable = money(max(subtotal - discount, Decimal("0")))
    return {
        "subtotal": subtotal,
        "discount": discount,
        "net_payable": net_payable,
        "discount_message": note if subtotal else "Add products to calculate the bill.",
    }


class SmartBillingApp:
    CATEGORIES = ["General", "Stationery", "Groceries", "Accessories", "Electronics", "Clothing"]

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Smart Billing & Discount Calculator")
        self.root.geometry("1120x750")
        self.root.minsize(980, 640)
        self.items: list[CartItem] = []
        self.selected_index: int | None = None
        self._configure_style()
        self._build_ui()
        self.refresh_cart()
        self.refresh_totals()

    def _configure_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 19, "bold"), foreground="#17365D")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 9), foreground="#526477")
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=27, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("Accent.TButton", font=("Segoe UI", 9, "bold"))

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Smart Billing & Discount Calculator", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Cart management  •  Manual discount calculation  •  Transparent bill summary",
                  style="Subtitle.TLabel").pack(anchor="w", pady=(3, 0))

        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)
        left, right = ttk.Frame(body), ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right.grid(row=0, column=1, sticky="nsew")
        self._build_product_form(left)
        self._build_cart(left)
        self._build_discount_panel(right)
        self._build_summary(right)
        self._build_actions(right)
        self.status_var = tk.StringVar(value="Ready. Add products to begin.")
        ttk.Label(outer, textvariable=self.status_var, relief="sunken", anchor="w", padding=5).pack(fill="x", pady=(10, 0))

    def _build_product_form(self, parent):
        box = ttk.LabelFrame(parent, text="Product Entry", padding=10, style="Section.TLabelframe")
        box.pack(fill="x", pady=(0, 10))
        self.desc_var = tk.StringVar()
        self.category_var = tk.StringVar(value="General")
        self.price_var = tk.StringVar()
        self.qty_var = tk.StringVar(value="1")
        ttk.Label(box, text="Product description").grid(row=0, column=0, sticky="w")
        ttk.Entry(box, textvariable=self.desc_var, width=28).grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(3, 8))
        ttk.Label(box, text="Category").grid(row=0, column=1, sticky="w")
        ttk.Combobox(box, textvariable=self.category_var, values=self.CATEGORIES, state="readonly", width=17).grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(3, 8))
        ttk.Label(box, text="Unit price (₹)").grid(row=0, column=2, sticky="w")
        ttk.Entry(box, textvariable=self.price_var, width=12).grid(row=1, column=2, sticky="ew", padx=(0, 8), pady=(3, 8))
        ttk.Label(box, text="Quantity").grid(row=0, column=3, sticky="w")
        ttk.Entry(box, textvariable=self.qty_var, width=8).grid(row=1, column=3, sticky="ew", pady=(3, 8))
        ttk.Button(box, text="Add to Cart", style="Accent.TButton", command=self.add_item).grid(row=2, column=0, sticky="ew", padx=(0, 5))
        ttk.Button(box, text="Clear Fields", command=self.clear_form).grid(row=2, column=1, sticky="ew", padx=(0, 5))
        ttk.Button(box, text="Update Selected", command=self.update_selected_item).grid(row=2, column=2, sticky="ew", padx=(0, 5))
        ttk.Button(box, text="Remove Selected", command=self.remove_selected_item).grid(row=2, column=3, sticky="ew")
        for col in range(4):
            box.columnconfigure(col, weight=1)

    def _build_cart(self, parent):
        box = ttk.LabelFrame(parent, text="Current Cart", padding=9, style="Section.TLabelframe")
        box.pack(fill="both", expand=True)
        cols = ("description", "category", "price", "qty", "total")
        self.tree = ttk.Treeview(box, columns=cols, show="headings", selectmode="browse")
        for key, title, width in [
            ("description", "Product", 180), ("category", "Category", 100),
            ("price", "Unit Price", 85), ("qty", "Qty", 50), ("total", "Line Total", 95)
        ]:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="w" if key in ("description", "category") else "e")
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_item)

    def _build_discount_panel(self, parent):
        box = ttk.LabelFrame(parent, text="Discount Settings", padding=10, style="Section.TLabelframe")
        box.pack(fill="x", pady=(0, 10))
        self.discount_type_var = tk.StringVar(value="None")
        self.discount_value_var = tk.StringVar(value="0")
        ttk.Label(box, text="Discount type").grid(row=0, column=0, sticky="w")
        ttk.Combobox(box, textvariable=self.discount_type_var,
                     values=["None", "Percentage", "Fixed Amount"], state="readonly").grid(
                         row=1, column=0, sticky="ew", padx=(0, 8), pady=(3, 8))
        ttk.Label(box, text="Discount value").grid(row=0, column=1, sticky="w")
        ttk.Entry(box, textvariable=self.discount_value_var).grid(
            row=1, column=1, sticky="ew", pady=(3, 8))
        ttk.Label(box, text="Percentage: enter 10 for 10%. Fixed Amount: enter rupees.",
                  foreground="#526477", wraplength=350).grid(row=2, column=0, columnspan=2, sticky="w")
        ttk.Button(box, text="Apply Discount", command=self.apply_discount).grid(
            row=3, column=0, sticky="ew", padx=(0, 8), pady=(8, 0))
        ttk.Button(box, text="Remove Discount", command=self.remove_discount).grid(
            row=3, column=1, sticky="ew", pady=(8, 0))
        box.columnconfigure(0, weight=1)
        box.columnconfigure(1, weight=1)

    def _build_summary(self, parent):
        box = ttk.LabelFrame(parent, text="Bill Summary", padding=12, style="Section.TLabelframe")
        box.pack(fill="x", pady=(0, 10))
        self.subtotal_var = tk.StringVar(value="₹ 0.00")
        self.discount_var = tk.StringVar(value="₹ 0.00")
        self.net_var = tk.StringVar(value="₹ 0.00")
        for label, var in [("Cart subtotal", self.subtotal_var), ("Discount / savings", self.discount_var)]:
            line = ttk.Frame(box)
            line.pack(fill="x", pady=4)
            ttk.Label(line, text=label).pack(side="left")
            ttk.Label(line, textvariable=var, font=("Segoe UI", 10, "bold")).pack(side="right")
        ttk.Separator(box).pack(fill="x", pady=7)
        line = ttk.Frame(box)
        line.pack(fill="x")
        ttk.Label(line, text="NET PAYABLE", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Label(line, textvariable=self.net_var, font=("Segoe UI", 16, "bold"), foreground="#167044").pack(side="right")
        self.summary_note = tk.StringVar(value="Add items to calculate the bill.")
        ttk.Label(box, textvariable=self.summary_note, wraplength=360, foreground="#526477").pack(anchor="w", pady=(8, 0))

    def _build_actions(self, parent):
        box = ttk.LabelFrame(parent, text="Bill Actions", padding=10, style="Section.TLabelframe")
        box.pack(fill="x")
        ttk.Button(box, text="Finalize & Save Bill", style="Accent.TButton", command=self.finalize_bill).pack(fill="x", pady=3)
        ttk.Button(box, text="Export Current Bill to CSV", command=self.export_current_bill).pack(fill="x", pady=3)
        ttk.Button(box, text="View Bill History", command=self.view_history).pack(fill="x", pady=3)
        ttk.Button(box, text="Clear Cart / New Bill", command=self.clear_cart).pack(fill="x", pady=3)

    def _read_form_item(self):
        description = self.desc_var.get().strip()
        category = self.category_var.get().strip()
        price = parse_decimal(self.price_var.get(), "Unit price")
        try:
            qty = int(self.qty_var.get().strip())
        except ValueError:
            raise ValueError("Quantity must be a positive whole number.")
        validate_item(description, category, price, qty)
        return CartItem(description, category, money(price), qty)

    def add_item(self):
        try:
            item = self._read_form_item()
        except ValueError as exc:
            messagebox.showerror("Invalid product", str(exc))
            return
        self.items.append(item)
        self.refresh_cart()
        self.refresh_totals()
        self.clear_form()
        self.status_var.set(f"Added {item.description} to the cart.")

    def update_selected_item(self):
        if self.selected_index is None or not (0 <= self.selected_index < len(self.items)):
            messagebox.showinfo("Select an item", "Choose a cart row before updating it.")
            return
        try:
            item = self._read_form_item()
        except ValueError as exc:
            messagebox.showerror("Invalid product", str(exc))
            return
        self.items[self.selected_index] = item
        self.refresh_cart()
        self.refresh_totals()
        self.clear_form()
        self.status_var.set("Selected cart item updated.")

    def remove_selected_item(self):
        if self.selected_index is None or not (0 <= self.selected_index < len(self.items)):
            messagebox.showinfo("Select an item", "Choose a cart row to remove.")
            return
        removed = self.items.pop(self.selected_index)
        self.selected_index = None
        self.refresh_cart()
        self.refresh_totals()
        self.clear_form()
        self.status_var.set(f"Removed {removed.description}.")

    def on_select_item(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        index = self.tree.index(selection[0])
        if index >= len(self.items):
            return
        self.selected_index = index
        item = self.items[index]
        self.desc_var.set(item.description)
        self.category_var.set(item.category)
        self.price_var.set(f"{item.unit_price:.2f}")
        self.qty_var.set(str(item.quantity))

    def clear_form(self):
        self.desc_var.set("")
        self.category_var.set("General")
        self.price_var.set("")
        self.qty_var.set("1")
        self.selected_index = None
        for selected in self.tree.selection():
            self.tree.selection_remove(selected)

    def _get_discount_settings(self):
        kind = self.discount_type_var.get()
        value = parse_decimal(self.discount_value_var.get() or "0", "Discount value")
        if value < 0:
            raise ValueError("Discount value cannot be negative.")
        if kind == "Percentage" and value > 100:
            raise ValueError("Percentage discount cannot exceed 100%.")
        return kind, value

    def apply_discount(self):
        try:
            kind, value = self._get_discount_settings()
            calculate_bill(self.items, kind, value)
        except ValueError as exc:
            messagebox.showerror("Invalid discount", str(exc))
            return
        self.refresh_totals()
        self.status_var.set("Discount settings applied.")

    def remove_discount(self):
        self.discount_type_var.set("None")
        self.discount_value_var.set("0")
        self.refresh_totals()
        self.status_var.set("Discount removed.")

    def refresh_cart(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for item in self.items:
            self.tree.insert("", "end", values=(
                item.description, item.category, f"{item.unit_price:.2f}",
                item.quantity, f"{item.line_total:.2f}"
            ))

    def refresh_totals(self):
        try:
            kind, value = self._get_discount_settings()
            result = calculate_bill(self.items, kind, value)
        except ValueError:
            result = calculate_bill(self.items)
        self.last_bill = result
        self.subtotal_var.set(f"₹ {result['subtotal']:.2f}")
        self.discount_var.set(f"₹ {result['discount']:.2f}")
        self.net_var.set(f"₹ {result['net_payable']:.2f}")
        self.summary_note.set(result["discount_message"])

    def _bill_record(self):
        kind, value = self._get_discount_settings()
        result = calculate_bill(self.items, kind, value)
        return {
            "bill_id": datetime.now().strftime("BILL-%Y%m%d-%H%M%S-%f"),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "currency": "INR",
            "items": [{
                "description": x.description, "category": x.category,
                "unit_price": str(x.unit_price), "quantity": x.quantity,
                "line_total": str(x.line_total)
            } for x in self.items],
            "discount_type": kind,
            "discount_value": str(value),
            "subtotal": str(result["subtotal"]),
            "discount": str(result["discount"]),
            "net_payable": str(result["net_payable"]),
            "discount_message": result["discount_message"],
        }

    def finalize_bill(self):
        if not self.items:
            messagebox.showwarning("Empty cart", "Add at least one product before finalizing a bill.")
            return
        try:
            record = self._bill_record()
        except ValueError as exc:
            messagebox.showerror("Invalid discount", str(exc))
            return
        history = self._load_history()
        history.append(record)
        try:
            HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save failed", f"Could not save bill history:\n{exc}")
            return
        self._show_receipt(record)
        self.status_var.set(f"Saved bill {record['bill_id']}.")

    def _show_receipt(self, record):
        win = tk.Toplevel(self.root)
        win.title("Bill Receipt")
        win.geometry("540x560")
        frame = ttk.Frame(win, padding=15)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="BILL RECEIPT", font=("Segoe UI", 17, "bold")).pack()
        ttk.Label(frame, text=f"{record['bill_id']}  |  {record['created_at']}").pack(pady=(2, 10))
        text = tk.Text(frame, height=20, wrap="none", font=("Courier New", 9))
        text.pack(fill="both", expand=True)
        text.insert("end", "Product                 Qty     Price      Amount\n")
        text.insert("end", "-" * 54 + "\n")
        for item in record["items"]:
            name = item["description"][:22]
            text.insert("end", f"{name:<22} {item['quantity']:>3} {Decimal(item['unit_price']):>9.2f} {Decimal(item['line_total']):>10.2f}\n")
        text.insert("end", "-" * 54 + "\n")
        text.insert("end", f"Subtotal:                         ₹ {Decimal(record['subtotal']):.2f}\n")
        text.insert("end", f"Discount ({record['discount_type']}):            ₹ {Decimal(record['discount']):.2f}\n")
        text.insert("end", f"NET PAYABLE:                      ₹ {Decimal(record['net_payable']):.2f}\n")
        text.insert("end", "\n" + record["discount_message"] + "\n")
        text.configure(state="disabled")
        ttk.Button(frame, text="Close", command=win.destroy).pack(pady=(10, 0))

    def export_current_bill(self):
        if not self.items:
            messagebox.showwarning("Empty cart", "There is no bill to export.")
            return
        try:
            record = self._bill_record()
        except ValueError as exc:
            messagebox.showerror("Invalid discount", str(exc))
            return
        path = filedialog.asksaveasfilename(
            title="Export bill", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")], initialfile="smart_billing_bill.csv"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Smart Billing & Discount Calculator"])
                writer.writerow(["Bill ID", record["bill_id"]])
                writer.writerow(["Created", record["created_at"]])
                writer.writerow([])
                writer.writerow(["Product", "Category", "Unit Price", "Quantity", "Line Total"])
                for item in record["items"]:
                    writer.writerow([item["description"], item["category"], item["unit_price"], item["quantity"], item["line_total"]])
                writer.writerow([])
                writer.writerow(["Discount Type", record["discount_type"]])
                writer.writerow(["Discount Value", record["discount_value"]])
                writer.writerow(["Subtotal", record["subtotal"]])
                writer.writerow(["Discount Amount", record["discount"]])
                writer.writerow(["Net Payable", record["net_payable"]])
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        self.status_var.set(f"Bill exported to {path}.")
        messagebox.showinfo("Export complete", "The bill was exported successfully.")

    def _load_history(self):
        if not HISTORY_FILE.exists():
            return []
        try:
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError):
            messagebox.showwarning("History warning", "Bill history could not be read. A new history file will be created.")
            return []

    def view_history(self):
        history = self._load_history()
        win = tk.Toplevel(self.root)
        win.title("Saved Bill History")
        win.geometry("760x420")
        frame = ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)
        cols = ("bill_id", "created", "subtotal", "discount", "net")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for key, label, width in [
            ("bill_id", "Bill ID", 230), ("created", "Created", 150),
            ("subtotal", "Subtotal", 100), ("discount", "Discount", 100), ("net", "Net Payable", 110)
        ]:
            tree.heading(key, text=label)
            tree.column(key, width=width, anchor="w" if key in ("bill_id", "created") else "e")
        tree.pack(fill="both", expand=True)
        for bill in reversed(history):
            tree.insert("", "end", values=(
                bill.get("bill_id", ""), bill.get("created_at", ""),
                bill.get("subtotal", ""), bill.get("discount", ""), bill.get("net_payable", "")
            ))
        if not history:
            ttk.Label(frame, text="No saved bills yet.").pack(pady=8)
        ttk.Button(frame, text="Close", command=win.destroy).pack(pady=(8, 0))

    def clear_cart(self):
        if self.items and not messagebox.askyesno("Clear cart", "Clear all items and start a new bill?"):
            return
        self.items.clear()
        self.remove_discount()
        self.clear_form()
        self.refresh_cart()
        self.refresh_totals()
        self.status_var.set("Cart cleared. Ready for a new bill.")


def main():
    root = tk.Tk()
    SmartBillingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
