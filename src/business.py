"""Descriptive campaign analysis and explicit, non-causal financial scenarios."""
from pathlib import Path
import json,sqlite3,itertools
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def scenario(trips,adoption,acceptance,incremental_share,price,margin,cost,coupon=0,k=8):
    impressions=trips*adoption*k
    accepted=impressions*acceptance
    incremental_items=accepted*incremental_share
    incremental_revenue=incremental_items*price
    coupon_cost=accepted*coupon
    profit=incremental_revenue*margin-coupon_cost-cost
    denominator=accepted*price*margin
    return dict(eligible_trips=trips,recommendations_per_eligible_day=k,adoption=adoption,acceptance=acceptance,incremental_share=incremental_share,
                item_price=price,margin_rate=margin,monthly_cost=cost,coupon_per_accepted_item=coupon,
                impressions=impressions,accepted_items=accepted,incremental_items=incremental_items,
                incremental_revenue=incremental_revenue,coupon_cost=coupon_cost,net_monthly_contribution=profit,
                break_even_incremental_share=(cost+coupon_cost)/denominator if denominator else None)

def run():
    cfg=json.loads((ROOT/'config/project.json').read_text());out=ROOT/'outputs'
    con=sqlite3.connect(ROOT/'data/processed/metropredict.sqlite')
    c=pd.read_csv(out/'campaign_performance.csv',dtype={'campaign_id':str})
    c['fully_observed']=(c.start_date>='2017-01-01')&(c.end_date<'2018-01-01')
    c['observation_note']=c.fully_observed.map({True:'Campaign fully inside source window',False:'Boundary campaign: redemption window truncated'})
    c.to_csv(out/'campaign_performance.csv',index=False)
    s=c[c.fully_observed].groupby('campaign_type').agg(campaigns=('campaign_id','size'),assigned_household_campaigns=('assigned_households','sum'),redeeming_household_campaigns=('redeeming_households','sum')).reset_index()
    s['household_campaign_redemption_rate']=s.redeeming_household_campaigns/s.assigned_household_campaigns
    s.to_csv(out/'campaign_types.csv',index=False)
    sql='''WITH eligible AS (
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
      FROM exposure GROUP BY campaign_id,campaign_type'''
    (ROOT/'sql/03_campaign_prepost.sql').write_text('-- Descriptive within-recipient change; no causal control group. Overlapping campaigns remain.\n'+sql+';\n')
    pd.read_sql_query(sql,con).to_csv(out/'campaign_prepost.csv',index=False)
    qa={
      'redemptions_without_assignment':int(con.execute('SELECT COUNT(*) FROM coupon_redemptions r LEFT JOIN campaigns a USING(campaign_id,household_id) WHERE a.campaign_id IS NULL').fetchone()[0]),
      'redemptions_outside_campaign_dates':int(con.execute('SELECT COUNT(*) FROM coupon_redemptions r JOIN campaign_descriptions d USING(campaign_id) WHERE date(r.redemption_date)<date(d.start_date) OR date(r.redemption_date)>date(d.end_date)').fetchone()[0]),
      'complete_campaigns':int(c.fully_observed.sum()),'boundary_campaigns':int((~c.fully_observed).sum())}
    (out/'campaign_audit.json').write_text(json.dumps(qa,indent=2));con.close()
    cost=cfg['monthly_operating_cost']+cfg['fixed_build_cost']/cfg['build_amortization_months']
    rows=[]
    policy=json.loads((out/'policy_results.json').read_text()) if (out/'policy_results.json').exists() else None
    capacities={'Fixed eight':cfg['k']}
    if policy and 'shown_items' in policy:capacities['Confidence filtered']=policy['shown_items']/policy['eligible_days']
    for capacity,adoption,acceptance,inc,margin,coupon in itertools.product(capacities,[.1,.25,.5],[.05,.1,.2],[.05,.1,.2,.4],[.15,.25,.35],[0,.5]):
        row=scenario(cfg['monthly_eligible_trips'],adoption,acceptance,inc,3.,margin,cost,coupon,capacities[capacity])
        row['capacity_policy']=capacity
        row['experience']='Reminders only' if coupon==0 else 'Reminders plus $0.50 coupon'
        rows.append(row)
    pd.DataFrame(rows).to_csv(out/'financial_scenarios.csv',index=False)
    central=scenario(cfg['monthly_eligible_trips'],.25,.1,.1,3.,cfg['assumed_margin_rate'],cost)
    (out/'financial_assumptions.json').write_text(json.dumps({'status':'Illustrative assumptions, not observed customer adoption or measured sales uplift',
       'central_scenario':central,'filtered_policy_scenario':scenario(cfg['monthly_eligible_trips'],.25,.1,.1,3.,cfg['assumed_margin_rate'],cost,k=capacities.get('Confidence filtered',8)),
       'operating_cost':cfg['monthly_operating_cost'],'one_time_build_cost':cfg['fixed_build_cost'],
       'amortization_months':cfg['build_amortization_months'],
       'incremental_share_definition':'Share of accepted suggestions that generate net additional retailer purchases over the evaluation horizon, after substitution and purchase timing effects.',
       'coupon_accounting':'Retailer-funded illustrative coupon charged on every accepted suggestion, including nonincremental purchases. Historical manufacturer coupon discounts are not assumed to be retailer costs.',
       'excluded':'Retention value, vendor funding, tax, inventory constraints and basket-wide halo effects are excluded.'},indent=2))
    print('Business outputs:',len(c),'campaigns;',len(rows),'scenarios',flush=True)

if __name__=='__main__':run()
