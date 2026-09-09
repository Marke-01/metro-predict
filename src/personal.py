"""Import Metro Market purchases later; no personal data is bundled.

Usage: python src/personal.py personal/my_purchases.csv --as-of YYYY-MM-DD
The default is a transparent replenishment rule. --model enables an explicitly
unvalidated transfer of the public-data model to behavior-based features.
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import pandas as pd
import joblib
from modeling import feature_vector,ROOT

def load_purchases(path):
    d=pd.read_csv(path,dtype={'product_id':str,'receipt_id':str})
    required=['purchase_date','product_name','quantity','sales_value']
    missing=set(required)-set(d.columns)
    if missing:raise ValueError('Missing columns: '+', '.join(sorted(missing)))
    if len(d)==0:raise ValueError('The import template is empty. Add your purchases first.')
    d['purchase_date']=pd.to_datetime(d.purchase_date,errors='raise').dt.normalize()
    if d.purchase_date.isna().any():raise ValueError('Missing purchase dates')
    if d.product_name.isna().any():raise ValueError('Missing product names')
    if 'product_id' not in d:d['product_id']=None
    d['product_id']=d.apply(lambda r:str(r.product_id) if pd.notna(r.product_id) else 'personal_'+hashlib.sha256(str(r.product_name).strip().lower().encode()).hexdigest()[:12],axis=1)
    for c in ['quantity','sales_value']:
        d[c]=pd.to_numeric(d[c],errors='raise')
        if not np.isfinite(d[c]).all():raise ValueError('Non-finite '+c)
    excluded=int(((d.quantity<=0)|(d.sales_value<0)).sum())
    d=d[(d.quantity>0)&(d.sales_value>=0)].copy()
    if d.empty:raise ValueError('No positive-quantity purchase rows remain')
    d['day']=(d.purchase_date-pd.Timestamp('2017-01-01')).dt.days
    return d,excluded

def predict(history,day,ntrips,firstday,lasttrip,model=None,k=8):
    ids=[p for p,h in history.items() if day-h['dates'][-1]<=180]
    ids=sorted(ids,key=lambda p:(-len(history[p]['dates']),-history[p]['dates'][-1],p))[:120]
    if not ids:return pd.DataFrame(columns=['product_id','score','rank'])
    x=np.asarray([feature_vector(history[p],day,ntrips,firstday,lasttrip) for p in ids],dtype=np.float32)
    score=model.predict_proba(x)[:,1] if model is not None else x[:,1]*np.minimum(x[:,6],2)
    d=pd.DataFrame({'product_id':ids,'score':score,'days_since_last':x[:,2],'median_interval':x[:,4],'prior_purchases':x[:,0]})
    d=d.sort_values(['score','product_id'],ascending=[False,True]).head(k).copy();d['rank']=range(1,len(d)+1)
    return d

def run(path,asof,use_model=False):
    d,excluded=load_purchases(path);history={};n=0;first=int(d.day.min());last=first;back=[]
    model=None
    if use_model:
        selection=json.loads((ROOT/'outputs/results.json').read_text())['selected_on_validation']
        if selection in ['Logistic regression','Gradient boosting']:
            model=joblib.load(ROOT/'models'/('logistic.joblib' if selection=='Logistic regression' else 'boosting.joblib'))
    for day,b in d.groupby('day',sort=True):
        if n>=5:
            pred=predict(history,int(day),n,first,last,model)
            actual=set(b.product_id);hit=int(pred.product_id.isin(actual).sum())
            if len(pred):back.append({'date':str(b.purchase_date.iloc[0].date()),'suggestions':len(pred),'hits':hit,'precision_shown':hit/len(pred),'recall_full_basket':hit/len(actual)})
        for p,bp in b.groupby('product_id'):
            h=history.setdefault(p,{'dates':[],'qty_sum':0});q=float(bp.quantity.sum());v=float(bp.sales_value.sum())
            h['dates'].append(int(day));h['qty_sum']+=q;h['last_qty']=q;h['last_unit_value']=v/q;h['trip_index']=n
        n+=1;last=int(day)
    date=pd.Timestamp(asof).normalize()
    if date<=d.purchase_date.max():raise ValueError('--as-of must be after the latest purchase date')
    pred=predict(history,int((date-pd.Timestamp('2017-01-01')).days),n,first,last,model)
    names=d.sort_values('purchase_date').drop_duplicates('product_id',keep='last')[['product_id','product_name']]
    pred=pred.merge(names,on='product_id',how='left',validate='one_to_one')
    out=ROOT/'personal/results';out.mkdir(exist_ok=True)
    pred.to_csv(out/'next_shopping_list.csv',index=False)
    pd.DataFrame(back).to_csv(out/'personal_backtest.csv',index=False)
    summary={'shopping_days':n,'valid_purchase_rows':len(d),'excluded_rows':excluded,'backtested_days':len(back),
        'mean_precision_shown':float(np.mean([x['precision_shown'] for x in back])) if back else None,
        'as_of':str(date.date()),'method':'Public model transfer (unvalidated calibration)' if model is not None else 'Personal-history replenishment rule',
        'limitations':'One household; variable-length lists differ from public Precision@8. Purchase gaps do not establish household inventory. Review brand/package aliases manually.'}
    (out/'personal_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('file');p.add_argument('--as-of',required=True);p.add_argument('--model',action='store_true');a=p.parse_args();run(a.file,a.as_of,a.model)
