# MetroPredict

**Independent grocery replenishment analytics, prepared by Eshwar Vudhanthi.**

Start with `reports/MetroPredict_Project_Report.pdf`. Open `tableau/MetroPredict.twbx` in Tableau 2026.1 or later for the editable workbook. Native Tableau opening was unavailable here; the workbook passes structural schema validation, not an application-level compatibility test.

## What the completed analysis found

- Analyzed **1,469,307 transactions from 2,469 households**, with **$4,596,039.58** in historical recorded sales.
- Built a SQLite warehouse and 17 past-only predictive features; modeled a deterministic sample of **800 households** across **1,685,532 candidate rows**.
- Compared frequent purchases, recent purchases, a replenishment rule, logistic regression and gradient boosting.
- On **6,233 held-out shopping days from 708 households**, gradient boosting achieved **16.47% Precision@8**, versus **15.18%** for the validation-selected frequency baseline: **8.54% relative gain**, or **1.30 percentage points**.
- A secondary confidence policy selected on validation reached **36.42% displayed-item precision** on test at **57.00% eligible-day coverage**, averaging **2.86 suggestions on covered days**.
- Analyzed **27 campaigns** and **432 explicit financial scenarios**. Campaign response is observational. Central assumed economics are negative. No sales uplift or profitable rollout is claimed.

**Decision: conditional, small learning pilot; no full launch.** The fixed-eight policy clears the relative-accuracy gate but produces only 1.32 matching products per shopping day. Confidence filtering offers a more selective experience. Economics and customer convenience must still be tested.

## Open the deliverables

| Item | File |
|---|---|
| Eight-page executive report | `reports/MetroPredict_Project_Report.pdf` |
| Editable Tableau package: six sheets, two dashboards | `tableau/MetroPredict.twbx` |
| Executed analysis notebook | `notebooks/MetroPredict_Analysis.ipynb` |
| SQL database | Generated locally at `data/processed/metropredict.sqlite` |
| SQL warehouse, analysis and campaign queries | `sql/` |
| Trained models | `models/logistic.joblib`, `models/boosting.joblib` |
| Test metrics and proposed recommendations | `outputs/` |
| Methodology, field definitions, limitations and pilot design | `docs/` |
| Personal-purchase template | `personal/purchases_template.csv` |

## Reproduce

Python 3.12 is recommended. Create a virtual environment, then run from this folder:

```bash
python -m pip install -r requirements.txt
python run_project.py
```

The full workflow takes several minutes or longer depending on hardware; allow several GB of RAM for feature creation and training. Raw public source files are bundled and checksum-verified. Network is needed only if original files are removed and must be downloaded again. The included model artifacts avoid retraining when you only want to inspect results. Large generated databases and feature matrices under `data/processed/` are intentionally excluded from Git and can be rebuilt with the command above.

Individual stages are in `src/`. The main pipeline order is warehouse, modeling, confidence policy, business scenarios, Tableau, report, notebook, tests. To inspect the existing database with Python:

```python
import sqlite3, pandas as pd
con = sqlite3.connect('data/processed/metropredict.sqlite')
print(pd.read_sql_query('SELECT * FROM v_customer_summary LIMIT 5', con))
```

Run validation independently:

```bash
python -m unittest discover -s tests -v
```

The notebook has executed cell outputs. To rerun it interactively, use your existing Jupyter installation or install Jupyter separately. Open it from this project or its `notebooks` folder.

## Interpretation rules

1. This is a public-data case study inspired by Metro Market; it is not a Metro Market production analysis or an affiliated project.
2. The Complete Journey package normalizes source dates onto 2017. It is not current retail data.
3. A shopping occasion is a household calendar day with eligible grocery purchases; multiple same-day receipts are combined.
4. Precision improvement is not additional revenue. Adoption, acceptance and net incrementality are separate financial inputs.
5. Coupons, prices and customer selection are not randomized here. No causal uplift model was fitted.
6. The confidence policy is exploratory follow-up, clearly separated from the frozen primary top-eight evaluation.
7. Your personal purchases have not yet been supplied. `docs/PERSONAL_DATA.md` explains the extension.

## Sources and attribution

Data originated from the 84.51° Complete Journey study. This release uses the [completejourney package](https://bradleyboehmke.github.io/completejourney/) by Brad Boehmke and Steven Mortimer, whose package declares CC0. See `docs/SOURCES.md` and `data/raw/manifest.json` for provenance and checksums. Original source data is distinguished from derived outputs. Analysis and implementation were prepared with AI assistance; interview claims should reflect your own review and understanding.
