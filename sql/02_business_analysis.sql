-- Run separately; every query is executable against data/processed/metropredict.sqlite.
-- Monthly historical performance; normalized dates, not a current retail forecast.
SELECT substr(shopping_date,1,7) AS month,COUNT(*) AS shopping_days,
 SUM(sales_value) AS sales_value,AVG(sales_value) AS average_day_value
FROM v_household_days GROUP BY month ORDER BY month;

-- Category scale and discount mix; do not interpret redemption as causation.
SELECT product_category,COUNT(*) AS lines,COUNT(DISTINCT household_id) AS households,
 SUM(sales_value) AS sales_value,SUM(retail_disc) AS retail_discount,
 SUM(coupon_disc) AS manufacturer_discount,SUM(coupon_match_disc) AS retailer_coupon_match
FROM v_sales_lines WHERE product_category IS NOT NULL
GROUP BY product_category ORDER BY sales_value DESC;

-- Product replenishment intervals; descriptive full-period query, never used
-- directly as training features. Modeling recalculates history at each cutoff.
SELECT product_id,COUNT(interval_days) AS repeat_intervals,AVG(interval_days) AS mean_interval_days
FROM v_purchase_intervals WHERE interval_days>0
GROUP BY product_id HAVING COUNT(interval_days)>=30 ORDER BY repeat_intervals DESC;

-- Campaign household response denominator: distinct assigned households.
WITH assigned AS (
 SELECT campaign_id,COUNT(DISTINCT household_id) AS assigned_households FROM campaigns GROUP BY campaign_id
), redeemed AS (
 SELECT r.campaign_id,COUNT(DISTINCT r.household_id) AS redeeming_households
 FROM coupon_redemptions r JOIN campaigns a USING(campaign_id,household_id)
 JOIN campaign_descriptions d USING(campaign_id)
 WHERE date(r.redemption_date) BETWEEN date(d.start_date) AND date(d.end_date)
 GROUP BY r.campaign_id
)
SELECT d.*,a.assigned_households,COALESCE(r.redeeming_households,0) AS redeeming_households,
 1.0*COALESCE(r.redeeming_households,0)/a.assigned_households AS household_redemption_rate
FROM campaign_descriptions d JOIN assigned a USING(campaign_id) LEFT JOIN redeemed r USING(campaign_id);
