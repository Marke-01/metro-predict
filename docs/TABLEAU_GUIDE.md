# Tableau workbook

Open `tableau/MetroPredict.twbx` in Tableau 2026.1 or later. The workbook was authored against the 2026.1 document format. The package includes six CSV sources in `Data/`; no database server or credentials are required. An unpackaged `MetroPredict.twb` and its matching `Data` folder are also supplied.

## Views

Executive decision dashboard: test model comparison, test category precision (top ten categories by suggestion count), illustrative economics for the confidence-filtered policy, and observational campaign-type response.

Analytical detail dashboard: validation threshold precision and historical monthly recorded sales. Six underlying worksheets remain editable. Selecting and hovering over marks provides Tableau's native inspection behavior; this release does not include cross-dashboard filter actions or user-editable financial parameters. For a different financial scenario, edit the CSV selection in `src/tableau_workbook.py` and rebuild, or connect `outputs/financial_scenarios.csv` directly and add the desired filters in Tableau.

## Validation boundary

The TWB is well-formed XML. Its local elements pass Tableau's official 2026.1 XSD. The published XSD imports user and XML namespaces without locations; the validation script supplies minimal definitions for `user:UserAttributes-AG` and `xml:base`, neither of which is used by this workbook. The official local-element definitions are unchanged. This check does not validate every connection attribute or guarantee application loading.

Native opening/rendering in Tableau Desktop, Public or Cloud was unavailable in the authoring environment. `outputs/tableau_validation.json` records that limitation. If your Tableau edition reports a connection path error, unpack the TWBX as a ZIP, open the TWB next to its `Data` folder, and use Edit Connection to point each view to the corresponding bundled CSV. This path repair is a contingency, not a claim that native loading has been verified.

The PDF contains verified chart renderings and all core results so you can assess the project immediately. Those charts are matplotlib renderings of the same outputs, not screenshots from Tableau.

## Data-source mapping

| CSV | Contents |
|---|---|
| view_1.csv | Test Precision@8 by model |
| view_2.csv | Test precision of suggestions by category |
| view_3.csv | Redemption per assigned household-campaign, complete campaigns only |
| view_4.csv | Confidence-filtered net monthly contribution under selected assumptions |
| view_5.csv | Validation item precision by threshold |
| view_6.csv | Full-department historical monthly sales |

Ratios are preaggregated at each plotted category and must not be summed across categories to create a total. For custom weighted totals, connect the underlying numerator/denominator files in `outputs/`.
