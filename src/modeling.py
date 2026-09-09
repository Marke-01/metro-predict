"""Time-ordered next-shopping-day ranking with three rules and two ML models."""
from pathlib import Path
import os
os.environ.setdefault('OMP_NUM_THREADS','4')
os.environ.setdefault('OPENBLAS_NUM_THREADS','4')
import json,sqlite3,hashlib,time,bisect
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score,roc_auc_score,brier_score_loss
import joblib
ROOT=Path(__file__).resolve().parents[1]
FEATURES=['purchase_count','purchase_rate','days_since_last','mean_interval','median_interval',
          'interval_cv','due_ratio','recent_30_count','recent_90_count','last_quantity',
          'mean_quantity','last_unit_value','prior_trips','history_days','days_since_trip',
          'trips_since_product','interval_known']

def feature_vector(h,day,ntrips,firstday,lasttrip):
    dates=h['dates']; gaps=np.diff(dates); known=len(gaps)>0
    mean=float(np.mean(gaps)) if known else 30.
    median=float(np.median(gaps)) if known else 30.
    rec=day-dates[-1]
    return [len(dates),len(dates)/ntrips,rec,mean,median,
            float(np.std(gaps)/mean) if known and mean>0 else 0.,min(rec/max(median,1),10),
            len(dates)-bisect.bisect_left(dates,day-30),len(dates)-bisect.bisect_left(dates,day-90),
            min(h['last_qty'],20),min(h['qty_sum']/len(dates),20),min(h['last_unit_value'],100),
            ntrips,day-firstday,day-lasttrip,ntrips-h['trip_index'],int(known)]

def make_features():
    cfg=json.loads((ROOT/'config/project.json').read_text())
    con=sqlite3.connect(ROOT/'data/processed/metropredict.sqlite')
    depts=','.join('?' for _ in cfg['departments'])
    tx=pd.read_sql_query(f'''SELECT household_id,shopping_date,product_id,SUM(quantity) quantity,SUM(sales_value) sales_value
     FROM v_sales_lines WHERE department IN ({depts}) AND product_category IS NOT NULL
     GROUP BY household_id,shopping_date,product_id ORDER BY household_id,shopping_date,product_id''',con,params=cfg['departments'])
    con.close()
    pool=tx.loc[tx.shopping_date<cfg['train_start'],'household_id'].unique()
    ids=sorted(pool,key=lambda s:hashlib.sha256(f"{cfg['seed']}:{s}".encode()).hexdigest())[:cfg['model_households']]
    (ROOT/'config/model_households.json').write_text(json.dumps(ids))
    tx=tx[tx.household_id.isin(ids)].copy()
    tx['day']=(pd.to_datetime(tx.shopping_date)-pd.Timestamp('2017-01-01')).dt.days
    records=[]; metadata=[]; coverage=[]; gid=0; max_source_gap=9999
    for hi,(hh,hdf) in enumerate(tx.groupby('household_id',sort=True)):
        history={}; ntrips=0;firstday=int(hdf.day.min());lasttrip=firstday
        for (date,day),basket in hdf.groupby(['shopping_date','day'],sort=True):
            split='train' if date<cfg['validation_start'] else 'validation' if date<cfg['test_start'] else 'test'
            target=date>=cfg['train_start'] and date<cfg['end_exclusive']
            chosen=split!='train' or ntrips%cfg['train_trip_stride']==0
            candidates=[p for p,h in history.items() if day-h['dates'][-1]<=cfg['candidate_lookback_days']]
            candidates=sorted(candidates,key=lambda p:(-len(history[p]['dates']),-history[p]['dates'][-1],p))[:cfg['max_candidates']]
            actual=set(basket.product_id)
            if target and chosen:
                eligible=ntrips>=cfg['min_prior_trips'] and len(candidates)>=cfg['k']
                coverage.append([hh,date,split,int(eligible),len(candidates),len(actual),len(actual & set(candidates))])
                if eligible:
                    for p in candidates:
                        h=history[p]; assert h['dates'][-1]<day
                        max_source_gap=min(max_source_gap,day-h['dates'][-1])
                        records.append(feature_vector(h,day,ntrips,firstday,lasttrip))
                        metadata.append([gid,hh,date,p,split,int(p in actual),len(actual),len(actual & set(candidates))])
                    gid+=1
            for p,qty,value in basket[['product_id','quantity','sales_value']].itertuples(index=False,name=None):
                h=history.setdefault(p,{'dates':[],'qty_sum':0})
                h['dates'].append(int(day));h['qty_sum']+=qty;h['last_qty']=qty;h['last_unit_value']=value/qty;h['trip_index']=ntrips
            ntrips+=1;lasttrip=day
        if (hi+1)%100==0: print('Feature households',hi+1,'candidate rows',len(records),flush=True)
    X=np.asarray(records,dtype=np.float32)
    meta=pd.DataFrame(metadata,columns=['group_id','household_id','date','product_id','split','actual','basket_items','candidate_actual_items'])
    cov=pd.DataFrame(coverage,columns=['household_id','date','split','eligible','candidates','basket_items','candidate_actual_items'])
    np.savez_compressed(ROOT/'data/processed/features.npz',X=X)
    meta.to_csv(ROOT/'data/processed/feature_metadata.csv.gz',index=False)
    cov.to_csv(ROOT/'outputs/eligibility.csv',index=False)
    (ROOT/'outputs/feature_audit.json').write_text(json.dumps({'features':FEATURES,'rows':len(meta),'groups':gid,'households':len(ids),'minimum_days_between_feature_source_and_target':int(max_source_gap),'split_candidate_rows':meta.split.value_counts().to_dict(),'split_groups':meta.groupby('split').group_id.nunique().to_dict()},indent=2))
    return X,meta,cov

def rank_metrics(meta,scores,k):
    d=meta.copy();d['score']=scores
    d=d.sort_values(['group_id','score','product_id'],ascending=[True,False,True],kind='stable')
    d['rank']=d.groupby('group_id').cumcount()+1
    top=d[d['rank']<=k].copy()
    top['discounted_hit']=top.actual/np.log2(top['rank']+1)
    g=top.groupby('group_id').agg(household_id=('household_id','first'),date=('date','first'),hits=('actual','sum'),
        basket_items=('basket_items','first'),candidate_actual_items=('candidate_actual_items','first'),dcg=('discounted_hit','sum'))
    g['precision_at_8']=g.hits/k
    g['recall_full_basket']=g.hits/g.basket_items
    g['recall_candidates']=g.hits/g.candidate_actual_items.replace(0,np.nan)
    idcg=np.array([sum(1/np.log2(np.arange(1,min(k,int(n))+1)+1)) for n in g.candidate_actual_items])
    g['ndcg_at_8']=np.divide(g.dcg,idcg,out=np.zeros(len(g)),where=idcg>0)
    return g.reset_index(),top

def bootstrap_delta(a,b,seed=42):
    d=a[['group_id','household_id','precision_at_8']].merge(b[['group_id','precision_at_8']],on='group_id',suffixes=('_a','_b'))
    d['delta']=d.precision_at_8_a-d.precision_at_8_b
    g=d.groupby('household_id').delta.agg(['sum','count']).to_numpy()
    rng=np.random.default_rng(seed);vals=[]
    for _ in range(2000):
        z=g[rng.integers(0,len(g),len(g))];vals.append(z[:,0].sum()/z[:,1].sum())
    return [float(x) for x in np.quantile(vals,[.025,.975])]

def run_models():
    cfg=json.loads((ROOT/'config/project.json').read_text());k=cfg['k']
    X,meta,cov=make_features();y=meta.actual.to_numpy()
    train=(meta.split=='train').to_numpy()
    models={'Logistic regression':make_pipeline(StandardScaler(),LogisticRegression(max_iter=350,C=1.0,random_state=cfg['seed'])),
            'Gradient boosting':HistGradientBoostingClassifier(max_iter=110,max_leaf_nodes=15,learning_rate=.08,l2_regularization=5,early_stopping=False,random_state=cfg['seed'])}
    for name,m in models.items():
        t=time.time();m.fit(X[train],y[train]);print('Trained',name,round(time.time()-t,1),'seconds',flush=True)
        joblib.dump(m,ROOT/'models'/('logistic.joblib' if name=='Logistic regression' else 'boosting.joblib'))
    summaries=[];all_trip=[];tops={};tripsets={};diagnostics=[];calibration=[]
    for split in ['validation','test']:
        mask=(meta.split==split).to_numpy();xm=X[mask];m=meta[mask]
        scores={'Frequent purchases':xm[:,1],
                'Recent purchases':-xm[:,2]+xm[:,1]*.001,
                'Replenishment rule':xm[:,1]*np.minimum(xm[:,6],2)}
        scores.update({n:model.predict_proba(xm)[:,1] for n,model in models.items()})
        for name,score in scores.items():
            g,top=rank_metrics(m,score,k);tripsets[(split,name)]=g;tops[(split,name)]=top
            g['model']=name;g['split']=split;all_trip.append(g)
            summaries.append({'split':split,'model':name,'shopping_days':len(g),'households':g.household_id.nunique(),
                'precision_at_8':g.precision_at_8.mean(),'recall_full_basket':g.recall_full_basket.mean(),
                'recall_candidates':g.recall_candidates.mean(),'ndcg_at_8':g.ndcg_at_8.mean(),'mean_hits':g.hits.mean()})
            if name in models:
                diagnostics.append({'split':split,'model':name,'pr_auc_average_precision':average_precision_score(y[mask],score),
                    'roc_auc':roc_auc_score(y[mask],score),'brier_score':brier_score_loss(y[mask],score),'positive_rate':float(y[mask].mean())})
                z=pd.DataFrame({'predicted':score,'actual':y[mask]});z['bin']=pd.cut(z.predicted,np.linspace(0,1,11),include_lowest=True)
                c=z.groupby('bin',observed=True).agg(predicted=('predicted','mean'),actual=('actual','mean'),count=('actual','size')).reset_index()
                c['bin']=c['bin'].astype(str);c['model']=name;c['split']=split;calibration.append(c)
    summary=pd.DataFrame(summaries);summary.to_csv(ROOT/'outputs/model_comparison.csv',index=False)
    val=summary[summary.split=='validation'].sort_values('precision_at_8',ascending=False)
    selected=val.iloc[0]['model'];simple=val[~val.model.isin(models)].iloc[0]['model']
    best=tripsets[('test',selected)];base=tripsets[('test',simple)]
    delta=float(best.precision_at_8.mean()-base.precision_at_8.mean())
    relative=delta/float(base.precision_at_8.mean());ci=bootstrap_delta(best,base)
    decision='PILOT' if relative>=cfg['pilot_relative_precision_gate'] and ci[0]>0 else 'MODIFY'
    result={'selected_on_validation':selected,'baseline_selected_on_validation':simple,'test_precision_at_8':float(best.precision_at_8.mean()),
            'test_baseline_precision_at_8':float(base.precision_at_8.mean()),'test_absolute_gain':delta,'test_relative_gain':relative,
            'cluster_bootstrap_95ci_absolute_gain':ci,'recommendation':decision,'test_shopping_days':len(best),'test_households':int(best.household_id.nunique()),
            'test_eligible_day_coverage':float(cov[cov.split=='test'].eligible.mean()),
            'decision_rule':'Pilot readiness requires >=5% relative Precision@8 gain and household-clustered 95% CI above zero. Economics and live effects remain unproven.'}
    (ROOT/'outputs/results.json').write_text(json.dumps(result,indent=2))
    pd.concat(all_trip).to_csv(ROOT/'outputs/trip_metrics.csv.gz',index=False)
    pd.DataFrame(diagnostics).to_csv(ROOT/'outputs/probability_diagnostics.csv',index=False)
    pd.concat(calibration).to_csv(ROOT/'outputs/calibration.csv',index=False)
    top=tops[('test',selected)].copy()
    products=pd.read_csv(ROOT/'data/raw/products.csv.gz',dtype={'product_id':str})
    top=top.merge(products,on='product_id',how='left',validate='many_to_one')
    top['score_type']='probability' if selected in models else 'ranking score'
    top['reason']='Repeat purchase history and purchase timing'
    top.to_csv(ROOT/'outputs/test_recommendations.csv.gz',index=False)
    seg=best.copy();seg['basket_segment']=pd.cut(seg.basket_items,[0,8,20,np.inf],labels=['1-8 products','9-20 products','21+ products'])
    seg.groupby('basket_segment',observed=True).agg(shopping_days=('group_id','size'),precision_at_8=('precision_at_8','mean'),recall_full_basket=('recall_full_basket','mean')).reset_index().to_csv(ROOT/'outputs/basket_segments.csv',index=False)
    top.groupby('product_category').agg(suggestions=('actual','size'),hits=('actual','sum'),precision=('actual','mean')).reset_index().sort_values('suggestions',ascending=False).to_csv(ROOT/'outputs/category_performance.csv',index=False)
    # Permutation importance on validation only, using top-k metric and at most 500 complete groups.
    if selected in models:
        vm=meta[meta.split=='validation'];gids=vm.group_id.unique()[:500]
        imask=((meta.split=='validation') & meta.group_id.isin(gids)).to_numpy();xi=X[imask].copy();mi=meta[imask]
        orig=rank_metrics(mi,models[selected].predict_proba(xi)[:,1],k)[0].precision_at_8.mean()
        rng=np.random.default_rng(cfg['seed']);importance=[]
        for j,f in enumerate(FEATURES):
            xp=xi.copy();rng.shuffle(xp[:,j]);p=rank_metrics(mi,models[selected].predict_proba(xp)[:,1],k)[0].precision_at_8.mean()
            importance.append({'feature':f,'validation_precision_drop':orig-p})
        pd.DataFrame(importance).sort_values('validation_precision_drop',ascending=False).to_csv(ROOT/'outputs/feature_importance.csv',index=False)
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':run_models()
