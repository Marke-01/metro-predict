# Sources and attribution

Retrieved for this project on September 6, 2026.

1. **Complete Journey package**, Brad Boehmke and Steven Mortimer; source study from 84.51°. Package declares CC0. https://bradleyboehmke.github.io/completejourney/
2. **Repository data**: https://github.com/bradleyboehmke/completejourney/tree/master/data . Six original R-format files are bundled. `data/raw/manifest.json` records the precise source URL, size and SHA-256 of every downloaded source. The downloader refuses a checksum mismatch. Derived CSVs are local conversions of these originals, not an independent dataset.
3. **Source preparation script**: https://github.com/bradleyboehmke/completejourney/blob/master/data-raw/prep-data.R . Explains the one-year slice, date normalization, timestamp construction, department cleaning and discount transformations. Source copies of relevant metadata documentation are in `docs/source/`.
4. **Original dataset context**: https://www.dunnhumby.com/source-files/ . The original two-year, 2,500-household description differs from the one-year package actually analyzed. The project reports the latter's observed counts.
5. **R serialization specification**: https://cran.r-project.org/doc/manuals/r-release/R-ints.html#Serialization-Formats . `src/read_r.py` implements only the vector and pairlist subset required by these pinned files, without R execution or extra packages. Unsupported types fail explicitly.
6. **Tableau official schemas**: https://github.com/tableau/tableau-document-schemas . The 2026.1 XSD is bundled solely for validation, with its license. The README distinguishes structural validation from successful opening in Tableau.
7. **Tableau workbook format and packaging**: https://help.tableau.com/current/pro/desktop/en-us/save_savework_packagedworkbooks.htm . The delivered TWBX is a ZIP containing a TWB and local CSV data.

## What is and is not claimed

No affiliation with Metro Market, Kroger, 84.51°, dunnhumby or Tableau. No personal loyalty history, current pricing, causal coupon uplift, measured adoption, measured retention or live sales effect is claimed. Financial assumptions are selected for sensitivity analysis, not sourced retailer financials. Attribution of project authorship should reflect AI assistance and Eshwar's subsequent review and contributions.

All model metrics in the report derive from the executed public-data pipeline. Figure sources are the corresponding CSV outputs. `outputs/runtime.json` captures exact library versions used here.
