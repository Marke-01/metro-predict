-- SQLite 3.25+; source tables loaded from pinned Complete Journey files.
-- Keep raw receipt rows intact. One model trip is a household shopping day.
CREATE INDEX IF NOT EXISTS ix_tx_hh_time ON transactions(household_id,transaction_timestamp);
CREATE UNIQUE INDEX IF NOT EXISTS ix_product ON products(product_id);
CREATE INDEX IF NOT EXISTS ix_tx_product ON transactions(product_id);
DROP VIEW IF EXISTS v_sales_lines;
CREATE VIEW v_sales_lines AS
SELECT t.*, substr(transaction_timestamp,1,10) AS shopping_date,
       p.department, p.product_category, p.product_type, p.package_size, p.brand,
       CASE WHEN quantity>0 THEN sales_value/quantity END AS unit_sales_value
FROM transactions t LEFT JOIN products p USING(product_id)
WHERE t.quantity>0 AND t.sales_value>=0;
DROP VIEW IF EXISTS v_household_days;
CREATE VIEW v_household_days AS
SELECT household_id,shopping_date,COUNT(DISTINCT basket_id) AS receipt_count,
       COUNT(DISTINCT product_id) AS distinct_products,SUM(sales_value) AS sales_value,
       SUM(retail_disc) AS retail_discount,SUM(coupon_disc) AS manufacturer_discount,
       SUM(coupon_match_disc) AS retailer_coupon_match
FROM v_sales_lines GROUP BY household_id,shopping_date;
DROP VIEW IF EXISTS v_purchase_intervals;
CREATE VIEW v_purchase_intervals AS
WITH product_days AS (
 SELECT household_id,product_id,shopping_date,SUM(quantity) AS quantity
 FROM v_sales_lines GROUP BY household_id,product_id,shopping_date
), lagged AS (
 SELECT *,LAG(shopping_date) OVER(PARTITION BY household_id,product_id ORDER BY shopping_date) AS previous_date
 FROM product_days
)
SELECT *,julianday(shopping_date)-julianday(previous_date) AS interval_days FROM lagged;
DROP VIEW IF EXISTS v_customer_summary;
CREATE VIEW v_customer_summary AS
SELECT household_id,COUNT(*) AS shopping_days,SUM(receipt_count) AS receipts,
       SUM(sales_value) AS sales_value,AVG(sales_value) AS average_day_value,
       MIN(shopping_date) AS first_date,MAX(shopping_date) AS last_date
FROM v_household_days GROUP BY household_id;
