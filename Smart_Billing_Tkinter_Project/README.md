# Smart Billing & Discount Calculator — Tkinter

A Python desktop billing application with cart management and a simple manual discount system. The coupon/promo-code system has been removed.

## Features
- Add, update, and remove cart products.
- Product categories, unit prices, and quantities.
- Automatic line totals and subtotal.
- Apply either a percentage discount or a fixed-amount discount.
- Remove the discount at any time.
- Discount is limited to the bill subtotal; payable amount cannot become negative.
- Receipt-style bill display.
- Save finalized bills locally in `bill_history.json`.
- Export the current bill to CSV.
- View saved bill history.

## Discount usage
1. Choose `Percentage` or `Fixed Amount`.
2. For a percentage discount, enter a number such as `10` for 10%.
3. For a fixed discount, enter the amount in rupees, such as `50`.
4. Click **Apply Discount**.
5. Click **Remove Discount** to reset it.

No coupon codes, coupon validation, minimum-spend rules, or category-specific promotions are used.

## Requirements
- Python 3.9 or later recommended.
- Tkinter.
- No third-party packages.

## Run
```bash
python smart_billing_app.py
```

## Tests
```bash
python -m unittest test_billing.py -v
```

Currency calculations use `Decimal` and round to two decimal places using `ROUND_HALF_UP`. Bill history is stored locally in `bill_history.json`.
