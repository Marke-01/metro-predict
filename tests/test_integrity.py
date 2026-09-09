"""Meaningful guards for historical isolation, source reconciliation and economics."""
import unittest,sys,json,sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
DATABASE=ROOT/'data/processed/metropredict.sqlite'
FEATURE_METADATA=ROOT/'data/processed/feature_metadata.csv.gz'
from personal import predict
from business import scenario
from modeling import rank_metrics

class IntegrityTests(unittest.TestCase):
    def test_pinned_source_totals(self):
        a=json.loads((ROOT/'outputs/data_audit.json').read_text())
        self.assertEqual(a['transactions']['rows'],1469307)
        self.assertEqual(a['source']['households'],2469)
        self.assertAlmostEqual(a['source']['sales_value'],4596039.58,places=2)
    @unittest.skipUnless(DATABASE.exists(), 'run the pipeline to generate the SQLite warehouse')
    def test_product_key_and_campaign_denominator(self):
        c=sqlite3.connect(DATABASE)
        self.assertEqual(c.execute('SELECT COUNT(*)-COUNT(DISTINCT product_id) FROM products').fetchone()[0],0)
        d=pd.read_csv(ROOT/'outputs/campaign_performance.csv')
        self.assertTrue((d.redeeming_households<=d.assigned_households).all())
        c.close()
    @unittest.skipUnless(FEATURE_METADATA.exists(), 'run the pipeline to generate feature metadata')
    def test_temporal_feature_boundary(self):
        a=json.loads((ROOT/'outputs/feature_audit.json').read_text())
        self.assertGreaterEqual(a['minimum_days_between_feature_source_and_target'],1)
        m=pd.read_csv(FEATURE_METADATA,usecols=['date','split'])
        self.assertLess(m[m.split=='train'].date.max(),m[m.split=='validation'].date.min())
        self.assertLess(m[m.split=='validation'].date.max(),m[m.split=='test'].date.min())
    def test_known_ranking_answer(self):
        d=pd.DataFrame({'group_id':[1]*10,'household_id':['x']*10,'date':['2017-12-01']*10,'product_id':list('abcdefghij'),
                        'actual':[1,0,1,0,1,0,0,1,1,1],'basket_items':[10]*10,'candidate_actual_items':[6]*10})
        g,top=rank_metrics(d,np.arange(10,0,-1),8)
        self.assertEqual(g.hits.iloc[0],4);self.assertEqual(g.precision_at_8.iloc[0],.5)
        self.assertEqual(g.recall_full_basket.iloc[0],.4)
    def test_zero_incrementality_cannot_create_profit(self):
        s=scenario(100000,.25,.1,0,3,.25,5000)
        self.assertEqual(s['incremental_revenue'],0);self.assertEqual(s['net_monthly_contribution'],-5000)
    def test_break_even_substitution(self):
        s=scenario(100000,.25,.1,.1,3,.25,5000)
        b=scenario(100000,.25,.1,s['break_even_incremental_share'],3,.25,5000)
        self.assertAlmostEqual(b['net_monthly_contribution'],0,places=8)
    def test_coupon_charged_to_nonincremental_purchases(self):
        s=scenario(100000,.25,.1,0,3,.25,5000,.5)
        self.assertEqual(s['coupon_cost'],10000);self.assertEqual(s['net_monthly_contribution'],-15000)
    def test_expired_candidate_not_shown(self):
        h={'old':{'dates':[0,10],'qty_sum':2,'last_qty':1,'last_unit_value':3,'trip_index':1},
           'new':{'dates':[185,195],'qty_sum':2,'last_qty':1,'last_unit_value':3,'trip_index':4}}
        p=predict(h,200,5,0,195)
        self.assertEqual(p.product_id.tolist(),['new'])

if __name__=='__main__':unittest.main(verbosity=2)
