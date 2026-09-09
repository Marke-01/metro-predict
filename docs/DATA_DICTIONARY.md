# Data dictionary

## Source tables

| Table | Grain / key | Main fields | Notes |
|---|---|---|---|
| transactions | Receipt item line; no invented unique source key | household_id, basket_id, store_id, product_id, quantity, sales_value, discounts, week, transaction_timestamp | All source rows retained; quantity is source units, not standardized weight |
| products | One row per product_id | manufacturer_id, department, brand, product_category, product_type, package_size | Brand is National/Private, not a brand name; descriptions are not full shelf names |
| campaigns | One household_id + campaign_id assignment | household_id, campaign_id | Assignment, not confirmed exposure |
| campaign_descriptions | One row per campaign_id | campaign_type, start_date, end_date | Dates can extend outside source transaction window |
| coupons | Coupon UPC + product_id + campaign_id mapping | coupon_upc, product_id, campaign_id | One coupon can map to multiple products; 4,872 exact duplicates retained in raw source |
| coupon_redemptions | Household redemption event | household_id, coupon_upc, campaign_id, redemption_date | Distinct household-campaign conversion used for response rates |

Identifiers are strings, including UPCs, to preserve identifier meaning. SQL source tables have SQLite indexes; views express the analytical layer.

## Important field definitions

- `sales_value`: source-documented amount the retailer receives from sale. It is not gross profit and should not automatically have all discounts subtracted again.
- `retail_disc`: prepared positive retailer loyalty discount amount.
- `coupon_disc`: prepared positive manufacturer coupon discount amount; do not automatically treat it as retailer expense.
- `coupon_match_disc`: prepared positive retailer matching discount.
- `shopping_date`: local-date portion of normalized transaction timestamp. Multiple receipts on that household-date form a shopping day.
- `unit_sales_value`: recorded line sales / source quantity for positive quantity. It is not normalized price per kilogram or another common unit.

## Modeling artifacts

`features.npz` holds the float32 feature matrix `X`. Row order matches `feature_metadata.csv.gz`. Column order is in `outputs/feature_audit.json` and `src/modeling.py:FEATURES`.

| Metadata field | Definition |
|---|---|
| group_id | Unique evaluated household-shopping-day snapshot |
| household_id | Source household identifier |
| date | Target shopping date |
| product_id | Previously purchased candidate product |
| split | train / validation / test |
| actual | 1 if that product was purchased on the target date |
| basket_items | All distinct model-scope grocery products on target day |
| candidate_actual_items | Actual products inside the eligible capped candidate set |

`test_recommendations.csv.gz` contains the selected model's top eight per eligible test day with score, rank, outcome, category and package metadata. `filtered_recommendations.csv.gz` contains only those at or above the validation-selected threshold. These are historical backtest outputs, not recommendations sent to customers.

## Output metrics and scenarios

- `model_comparison.csv`: one row per model and validation/test split; day-averaged ranking metrics.
- `trip_metrics.csv.gz`: one row per model, split and evaluated day; supports paired comparisons.
- `eligibility.csv`: eligibility and candidate coverage for sampled target snapshots; training is subsampled every third occasion, validation/test are not.
- `category_performance.csv`: total suggestions and hits by category, using the fixed-eight policy. Precision = hits / suggestions.
- `basket_segments.csv`: realized basket-size diagnostics, not pre-purchase targeting features.
- `campaign_performance.csv`: campaign assignment denominator, redeemed-household count, rate and boundary flag.
- `campaign_types.csv`: complete-campaign aggregate household-campaign rates. A household in two campaigns counts twice, once per assignment.
- `campaign_prepost.csv`: mean 28-day spending before and during eligible campaigns among recipients; descriptive only.
- `financial_scenarios.csv`: 432 rows of explicitly assumed behavior and costs; two list-capacity policies × three adoption levels × three acceptance levels × four incrementality levels × three margins × two coupon amounts.
- `capacity_policy`: fixed eight or confidence filtered. The latter uses test shown items / eligible days as a capacity illustration, not as a guaranteed deployment rate.
- `break_even_incremental_share`: required net incremental fraction of accepted items to cover assumed coupon and monthly costs. Values >1 are infeasible under that scenario.

## Financial equations

```text
impressions = eligible_days × adoption × suggestions_per_eligible_day
accepted_items = impressions × acceptance
net_incremental_items = accepted_items × net_incremental_share
incremental_revenue = net_incremental_items × assumed_item_value
coupon_cost = accepted_items × assumed_retailer_coupon
net_contribution = incremental_revenue × assumed_margin - coupon_cost - monthly_cost
break_even_incremental_share = (monthly_cost + coupon_cost) /
                               (accepted_items × assumed_item_value × assumed_margin)
```

If the denominator is zero, break-even is undefined (null). Net incrementality is defined after displacement of other purchases and earlier/later timing effects. No retention value is added.
