# Methodology and reproducibility

## Frozen primary question
At the beginning of an observed household grocery shopping day, can history predict which previously purchased product IDs will appear that day better than a simple frequently-purchased list?

The task is conditional on a shopping occasion. It does not predict whether or when the next store visit will happen, pantry stock, or purchases at other retailers.

## Units and cleaning
Raw receipt lines remain in `transactions`. Purchase analysis excludes quantity <= 0 and sales_value < 0. Missing product metadata and unknown categories are excluded from modeling. Grocery department selection is explicit in `config/project.json`. Departments outside that list remain in the broader sales and campaign analyses. Aggregate all receipts for a household on a date before predicting; this avoids within-day leakage and dependence on source-generated timestamp seconds.

The source package turns discount fields positive and sets original positive retailer-discount anomalies to zero. This project uses those prepared values as documented; it cannot reconstruct the original anomalies. It does not infer product cost from sales.

## Sample and time split
Hash `42:household_id` with SHA-256 for households with eligible grocery purchases before April 1; take the first 800 sorted hashes. Selection never uses validation/test activity. Config and the chosen IDs are bundled. Some selected households do not shop in the test window; 708 contribute eligible test days. Coverage is conditional on observed days in the selected sample, not the retailer's entire customer base.

- Jan-Mar: history; no training labels.
- Apr-Sep: train on every third observed prior-trip count, reducing repeated similar observations.
- October: validation of fixed model choices and selection of the strongest simple baseline.
- Nov-Dec: fixed-model test. Earlier test purchases update history after their day has been scored, matching an operational rolling-history system. Model weights do not update.

Training labels are next-observed-day outcomes relative to prior history. They are created only after historical features. No random row split, full-period purchase averages, future quantity, current-basket value, future campaign redemption or customer demographics enter model features.

## Candidate generation
Require at least five prior eligible grocery shopping days. Candidate set = previously purchased products seen within the last 180 days. Keep at most 120, sorted by past purchase-day count, then most-recent purchase day and product ID. Require at least eight candidates for the primary comparison. This limits memory and explicitly accepts incomplete candidate coverage. Future new products cannot be recommended. No stock-availability data is present.

## Features
Seventeen numeric features: product purchase-day count, count/prior shopping days, days since purchase, mean/median past interval, interval coefficient of variation, elapsed/median interval ratio capped at 10, past 30/90-day purchase counts, last/mean quantity capped at 20, last recorded unit value capped at 100, prior day count, observed history span, days since last shopping day, shopping days since last product purchase, and interval-known flag. One-purchase histories use a 30-day interval fallback plus the flag. No current-day values enter these features.

## Models and selection
- Frequency score = past product purchase-day count / prior shopping days.
- Recency score = negative days since purchase with a tiny frequency tie-break.
- Replenishment rule = historical purchase rate × min(elapsed/median interval, 2).
- Standardized logistic regression: C=1, max_iter=350, no class reweighting.
- Histogram gradient boosting: 110 iterations, 15 leaves, learning rate .08, L2=5, no random internal early-stopping split.

No model hyperparameter search on test. All candidate rows are retained; no negative sampling or class weighting changes prevalence. Highest validation mean Precision@8 chooses the model; the strongest simple rule is selected independently on validation. Report every model's test result for transparency, with no post-test winner switch.

## Metrics
Precision@8 = correct top-eight suggestions / 8, averaged over shopping days. Full-basket recall = correct suggestions / all distinct eligible grocery products actually purchased that day, including new products and those outside the candidate cap. Candidate recall divides by the number of purchased candidate products; days with zero actual candidates are excluded from this recall average. NDCG@8 uses binary relevance and an ideal ordering within the candidate set; zero-relevant-candidate days receive zero. All models share exactly the same evaluated groups.

Uncertainty: 2,000 paired bootstrap samples of households with replacement. Each resample retains household-specific sums and counts of day-level precision differences, preserving the trip-weighted estimand and within-household dependence. This interval addresses the observed sample; it does not measure deployment distribution shift.

The project-defined primary gate is >=5% relative precision improvement and a clustered 95% interval above zero. It is an offline gate, not a retailer-approved commercial threshold. Gradient boosting meets it. Absolute accuracy and economics constrain the final recommendation to a conditional, small pilot.

## Secondary policy
After examining the primary benchmark, evaluate thresholds [.15,.20,.25,.30,.35,.40,.50] on validation scores from the selected model. Require >=35% item-weighted precision and >=100 covered validation days; choose maximum coverage. Fix the selected .30 threshold and evaluate it on test. This policy is explicitly exploratory, not preregistered as part of the primary gate. It offers at most eight items and abstains below threshold.

Precision here weights displayed items, so it is not directly comparable to day-averaged Precision@8 without considering coverage and list length. Overall eligible-day coverage of the primary study is about 99.3%; the policy covers about 57.0% of those eligible days, not 57% of all customers. Calibration metrics are descriptive; score values should not be presented as certain household needs.

## Interpretation limits
Realized basket-size groups are ex-post diagnostics and cannot be used to target an upcoming trip. Category results have differing support and are exploratory, without multiple-comparison claims. Feature permutation importance uses validation Precision@8 on up to 500 complete groups, one seeded permutation per feature; correlated features make it descriptive, not causal. Frequent purchase rate remains the strongest feature.
