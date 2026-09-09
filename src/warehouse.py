"""Convert pinned R sources to CSV and build the SQL warehouse + auditable QA."""
from pathlib import Path
import json,sqlite3,hashlib
import pandas as pd
from read_r import read_frame
ROOT=Path(__file__).resolve().parents[1]

def build():
    raw=ROOT/'data/raw';out=ROOT/'outputs'
    con=sqlite3.connect(ROOT/'data/processed/metropredict.sqlite')
    audit={}
    for name in ['transactions','products','campaigns','campaign_descriptions','coupons','coupon_redemptions']:
        f=raw/f'{name}.csv.gz'
        if not f.exists():
            ext='rds' if name=='transactions' else 'rda'
            read_frame(raw/f'{name}.{ext}').to_csv(f,index=False)
        df=pd.read_csv(f,dtype={c:str for c in ['household_id','store_id','basket_id','product_id','campaign_id','coupon_upc','manufacturer_id']})
        audit[name]={'rows':len(df),'exact_duplicate_rows':int(df.duplicated().sum()),'null_counts':df.isna().sum().to_dict()}
        df.to_sql(name,con,if_exists='replace',index=False,chunksize=10000)
    con.executescript((ROOT/'sql/01_warehouse.sql').read_text())
    q=lambda s:pd.read_sql_query(s,con)
    audit['source']={'households':int(q('SELECT COUNT(DISTINCT household_id) n FROM transactions').iloc[0,0]),
                     'baskets':int(q('SELECT COUNT(DISTINCT basket_id) n FROM transactions').iloc[0,0]),
                     'date_min':q('SELECT MIN(transaction_timestamp) FROM transactions').iloc[0,0],
                     'date_max':q('SELECT MAX(transaction_timestamp) FROM transactions').iloc[0,0],
                     'sales_value':float(q('SELECT SUM(sales_value) FROM transactions').iloc[0,0]),
                     'excluded_nonpositive_quantity_or_negative_sales':int(q('SELECT COUNT(*) FROM transactions WHERE quantity<=0 OR sales_value<0').iloc[0,0]),
                     'missing_product_metadata_lines':int(q('SELECT COUNT(*) FROM transactions t LEFT JOIN products p USING(product_id) WHERE p.product_id IS NULL').iloc[0,0])}
    queries='\n'.join(line for line in (ROOT/'sql/02_business_analysis.sql').read_text().splitlines() if not line.lstrip().startswith('--')).split(';')
    for name,sql in zip(['monthly_sales','category_sales','repurchase_intervals','campaign_performance'],[s for s in queries if 'SELECT' in s]):
        q(sql).to_csv(out/f'{name}.csv',index=False)
    q('SELECT * FROM v_customer_summary').to_csv(out/'customer_summary.csv',index=False)
    audit['source']['shopping_days']=int(q('SELECT COUNT(*) FROM v_household_days').iloc[0,0])
    (out/'data_audit.json').write_text(json.dumps(audit,indent=2))
    con.close();print(json.dumps(audit['source'],indent=2),flush=True)

if __name__=='__main__':build()
