# Add your Metro Market purchases later

No personal purchases are included in this project. The template contains headers only.

1. Copy `personal/purchases_template.csv` to `personal/my_purchases.csv`.
2. Add one receipt item per row. Required: `purchase_date` (YYYY-MM-DD), `product_name`, `quantity`, `sales_value` (line value, not unit price). Optional: receipt ID, product ID, retail discount and coupon discount. Discount columns are retained as optional input context; the personal scoring workflow currently uses quantities and recorded sales values only.
3. Preserve the same product ID for the same brand and size across trips. Without an ID, the script uses a deterministic hash of the normalized product name. It does not automatically merge differently abbreviated names. Review aliases and package changes manually.
4. Remove payment-card details, addresses and loyalty account numbers before adding data you intend to share.
5. Run, using a date after the latest purchase:

```bash
python src/personal.py personal/my_purchases.csv --as-of YYYY-MM-DD
```

Outputs in `personal/results/`: suggested next shopping list, rolling personal backtest and summary. The default is an interpretable rule using your own history. Backtesting begins after five shopping days, and lists may contain fewer than eight items. Its displayed-list precision differs from the public fixed-eight benchmark. Zero/negative quantity or negative-sale rows are excluded and counted. Blank template inputs fail clearly.

For an explicitly experimental public-model transfer:

```bash
python src/personal.py personal/my_purchases.csv --as-of YYYY-MM-DD --model
```

The numeric model does not require public SKU IDs, but its calibration may not transfer to your shopping history. The two datasets are not treated as one identified retailer population. The current transfer mode does not apply the public confidence threshold because calibration has not been validated for you. When your receipts arrive, review data consistency, product aliases, coverage and rolling predictions before making claims.

Shopping history alone cannot reveal purchases elsewhere, current inventory, stockouts or changes in preference. The recommendations should remain optional reminders.
