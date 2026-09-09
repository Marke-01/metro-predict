"""Secondary UX analysis: choose a confidence threshold on validation only.

This is exploratory follow-up to the frozen primary top-eight benchmark; it is
not part of the predeclared primary gate. Test output is a single fixed-policy
evaluation after validation selection. Precision here is per displayed item.
"""
from pathlib import Path
import json,joblib
import numpy as np
import pandas as pd
from modeling import ROOT,rank_metrics

def summarize(top,threshold):
    shown=top[top.score>=threshold]
    return {'threshold':threshold,'shown_items':len(shown),'covered_days':shown.group_id.nunique(),
            'eligible_days':top.group_id.nunique(),'day_coverage':shown.group_id.nunique()/top.group_id.nunique(),
            'displayed_item_precision':float(shown.actual.mean()) if len(shown) else None,
            'suggestions_per_covered_day':len(shown)/shown.group_id.nunique() if len(shown) else 0}

def run():
    selection=json.loads((ROOT/'outputs/results.json').read_text())['selected_on_validation']
    if selection not in ['Gradient boosting','Logistic regression']:return
    model=joblib.load(ROOT/'models'/('boosting.joblib' if selection=='Gradient boosting' else 'logistic.joblib'))
    meta=pd.read_csv(ROOT/'data/processed/feature_metadata.csv.gz',dtype={'household_id':str,'product_id':str})
    X=np.load(ROOT/'data/processed/features.npz')['X'];mask=(meta.split=='validation').to_numpy()
    _,valtop=rank_metrics(meta[mask],model.predict_proba(X[mask])[:,1],8)
    candidates=pd.DataFrame([summarize(valtop,t) for t in [.15,.2,.25,.3,.35,.4,.5]])
    candidates.to_csv(ROOT/'outputs/policy_validation.csv',index=False)
    feasible=candidates[(candidates.displayed_item_precision>=.35)&(candidates.covered_days>=100)]
    if feasible.empty:
        (ROOT/'outputs/policy_results.json').write_text(json.dumps({'status':'No threshold met exploratory validation requirements'}));return
    threshold=float(feasible.sort_values('day_coverage',ascending=False).iloc[0].threshold)
    testtop=pd.read_csv(ROOT/'outputs/test_recommendations.csv.gz',dtype={'household_id':str,'product_id':str})
    result=summarize(testtop,threshold)
    result.update({'status':'Exploratory threshold selected on validation','selection_rule':'Among predefined thresholds with >=35% displayed-item validation precision and >=100 covered days, maximize validation day coverage.','validation_precision':float(feasible[feasible.threshold==threshold].iloc[0].displayed_item_precision)})
    (ROOT/'outputs/policy_results.json').write_text(json.dumps(result,indent=2))
    testtop[testtop.score>=threshold].to_csv(ROOT/'outputs/filtered_recommendations.csv.gz',index=False)
    print(json.dumps(result,indent=2))
if __name__=='__main__':run()
