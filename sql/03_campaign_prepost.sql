-- Descriptive within-recipient change; no causal control group. Overlapping campaigns remain.
WITH eligible AS (
      SELECT * FROM campaign_descriptions WHERE date(start_date)>='2017-01-29'
       AND date(start_date,'+27 day')<=date(end_date) AND date(start_date,'+27 day')<='2017-12-31'
    ), exposure AS (
      SELECT a.household_id,a.campaign_id,d.campaign_type,d.start_date,
       COALESCE(SUM(CASE WHEN date(t.shopping_date)<date(d.start_date) THEN t.sales_value ELSE 0 END),0) AS pre_sales,
       COALESCE(SUM(CASE WHEN date(t.shopping_date)>=date(d.start_date) THEN t.sales_value ELSE 0 END),0) AS during_sales
      FROM campaigns a JOIN eligible d USING(campaign_id)
      LEFT JOIN v_household_days t ON t.household_id=a.household_id
       AND date(t.shopping_date) BETWEEN date(d.start_date,'-28 day') AND date(d.start_date,'+27 day')
      GROUP BY a.household_id,a.campaign_id,d.campaign_type,d.start_date
    ) SELECT campaign_id,campaign_type,COUNT(*) AS households,AVG(pre_sales) AS average_pre_28d_sales,
       AVG(during_sales) AS average_first_28d_sales,AVG(during_sales-pre_sales) AS observed_change
      FROM exposure GROUP BY campaign_id,campaign_type;
