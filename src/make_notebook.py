"""Create an actually executed notebook from the completed project outputs.

Cells execute locally; the final expression is rendered as text/table/image.
No separate Jupyter installation is required to build this notebook artifact.
"""
from pathlib import Path
import ast,base64,contextlib,io,json,traceback
import pandas as pd
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
CELLS=[
('markdown','# MetroPredict: measured retail analytics\n\nIndependent case study prepared for Eshwar Vudhanthi. This notebook inspects the executed pipeline. Run `python run_project.py` from the project root to rebuild training and outputs. Public data only; no Metro Market receipts.\n\n**Decision:** conditional pilot with a confidence-filtered list. Predictive gains are measured; revenue uplift is not.'),
('code','from pathlib import Path\nimport json, sqlite3\nimport pandas as pd\nfrom PIL import Image\nROOT = Path.cwd()\nif ROOT.name == "notebooks": ROOT = ROOT.parent\nassert (ROOT / "outputs/results.json").exists(), "Open from MetroPredict or its notebooks folder"\nresults = json.loads((ROOT / "outputs/results.json").read_text())\nresults'),
('markdown','## Source audit\nThe source has normalized 2017 dates and 2,469 households. Returns and invalid purchase rows are excluded from modeling. The coupon mapping has duplicates, so sales must never be joined directly to all coupon-product rows.'),
('code','audit = json.loads((ROOT / "outputs/data_audit.json").read_text())\npd.DataFrame([audit["source"]]).T'),
('markdown','## SQL: category scale\nThe query runs against the delivered SQLite warehouse. Recorded sales are historical; they are not retailer profit.'),
('code','con = sqlite3.connect(ROOT / "data/processed/metropredict.sqlite")\ncategory = pd.read_sql_query("""SELECT product_category, COUNT(DISTINCT household_id) households, ROUND(SUM(sales_value),2) sales_value FROM v_sales_lines WHERE product_category IS NOT NULL GROUP BY product_category ORDER BY sales_value DESC LIMIT 10""", con)\ncon.close()\ncategory'),
('markdown','## Frozen model comparison\nTrain April-September; select on October; test November-December. Three rules compete with logistic regression and gradient boosting. Each test day is scored from strictly earlier history. Precision@8 is averaged over shopping days.'),
('code','comparison = pd.read_csv(ROOT / "outputs/model_comparison.csv")\ncomparison.loc[comparison["split"] == "test", ["model", "shopping_days", "precision_at_8", "recall_full_basket", "mean_hits"]]'),
('code','Image.open(ROOT / "reports/figures/model_comparison.png")'),
('markdown','## Confidence-filtered policy\nThis is a secondary exploratory analysis. Threshold 0.30 was selected on validation, then evaluated once on test. Displayed-item precision and eligible-day coverage must be interpreted together.'),
('code','policy = json.loads((ROOT / "outputs/policy_results.json").read_text())\npolicy'),
('markdown','## Promotions: observational response\nDenominator is household-campaign assignment. Boundary campaigns are excluded below. These rates do not measure causal uplift or campaign profitability.'),
('code','pd.read_csv(ROOT / "outputs/campaign_types.csv")'),
('markdown','## Financial sensitivity\nAll behavioral and cost inputs are explicit assumptions. Accepted recommendations only create additional revenue to the extent that they change purchases after substitution and timing effects. The filtered capacity includes days with no suggestions.'),
('code','finance = pd.read_csv(ROOT / "outputs/financial_scenarios.csv")\ncentral = finance[(finance.adoption == .25) & (finance.acceptance == .1) & (finance.incremental_share == .1) & (finance.margin_rate == .25) & (finance.coupon_per_accepted_item == 0)]\ncentral[["capacity_policy", "recommendations_per_eligible_day", "accepted_items", "incremental_revenue", "net_monthly_contribution", "break_even_incremental_share"]]'),
('code','Image.open(ROOT / "reports/figures/financial_sensitivity.png")'),
('markdown','## Next business decision\nUse a budget-capped household-randomized experiment comparing existing purchase history, reminders alone, and reminders plus offers. Measure convenience and net contribution over a prespecified horizon. Do not convert the 8.5% ranking improvement into a sales-lift claim.\n\nYour purchases can be added using `personal/purchases_template.csv`; see `docs/PERSONAL_DATA.md`. Full methodology, source checksums, tests and Tableau validation limitations accompany this notebook.')]

def run():
    import os
    old=Path.cwd();os.chdir(ROOT)
    env={};cells=[];count=0
    try:
        for kind,source in CELLS:
            if kind=='markdown':cells.append({'cell_type':'markdown','metadata':{},'source':source.splitlines(True)});continue
            count+=1;stream=io.StringIO();outputs=[];tree=ast.parse(source)
            final=tree.body.pop() if tree.body and isinstance(tree.body[-1],ast.Expr) else None
            with contextlib.redirect_stdout(stream):
                exec(compile(tree,'<notebook-cell>','exec'),env)
                value=eval(compile(ast.Expression(final.value),'<notebook-cell>','eval'),env) if final else None
            if stream.getvalue():outputs.append({'output_type':'stream','name':'stdout','text':stream.getvalue().splitlines(True)})
            if value is not None:
                data={'text/plain':[repr(value)]}
                if isinstance(value,pd.DataFrame):data['text/html']=[value.to_html()]
                if isinstance(value,Image.Image):
                    b=io.BytesIO();value.save(b,format='PNG');data['image/png']=base64.b64encode(b.getvalue()).decode()
                outputs.append({'output_type':'execute_result','execution_count':count,'metadata':{},'data':data})
            cells.append({'cell_type':'code','execution_count':count,'metadata':{},'source':source.splitlines(True),'outputs':outputs})
        notebook={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12.11'},'metropredict':{'executed':True,'execution_method':'Local Python AST cell runner; outputs captured from actual execution'}},'nbformat':4,'nbformat_minor':5}
        for i,c in enumerate(cells):c['id']=f'metropredict-{i:02d}'
        (ROOT/'notebooks/MetroPredict_Analysis.ipynb').write_text(json.dumps(notebook,indent=1))
        print('Executed notebook:',count,'code cells')
    finally:os.chdir(old)
if __name__=='__main__':run()
