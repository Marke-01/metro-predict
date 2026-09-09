# Presenting MetroPredict

## A defensible short explanation
“I explored whether purchase timing could improve a grocery customer's suggested shopping list. The project analyzes 1.47 million public transactions with SQL and compares simple rules with Python models. The best model improved Precision@8 by 8.5% relative to frequency on a later test period. Because absolute accuracy was limited, I evaluated a shorter confidence-filtered list and recommended a selective pilot. I kept historical coupon response separate from causal lift and showed why the central business assumptions did not justify a broad launch.”

Use first-person implementation claims only after reviewing the code and being comfortable explaining and modifying it. The project was prepared with AI assistance.

## Questions worth preparing for

1. **Why not overall accuracy?** About 96% of candidate rows are negatives. A model predicting no purchases could look accurate but produce no useful ranked list.
2. **Why a time split?** The product must predict future purchases from earlier history. Random splitting would allow repeated customer patterns and future-derived statistics into evaluation.
3. **Why compare simple rules?** Complexity must earn its place. Frequency is a strong benchmark; the intuitive replenishment rule actually underperformed it.
4. **What does 8.5% improvement mean?** Relative Precision@8 gain, from 15.18% to 16.47%, or about 0.104 additional matches in an eight-item list. It is not an 8.5% sales increase.
5. **Why is accuracy still low?** Exact SKU matching, small baskets, new products and missing outside-retailer purchases all limit prediction. A fixed eight-item list also forces low-confidence suggestions.
6. **What changed with confidence filtering?** Test displayed-item precision rose to 36.4%, but only 57.0% of eligible days got suggestions. It is a different metric and a coverage tradeoff.
7. **Did coupons work?** Redemption differed between observed campaign groups. Selection and exposure are not randomized, so the project cannot establish causal purchase lift.
8. **Why a pilot if central economics are negative?** Only a low-cost learning pilot with a convenience objective is defensible. A broad profit-led rollout is not supported by current assumptions.
9. **What would your own receipts add?** A small real-world demonstration and transferability check, not enough data to claim retailer-wide performance.
10. **What would you improve next?** Review catalog equivalence, available products, household changes, more history-based targeting, and a randomized experiment with actual costs.

## Evidence-based resume bullet after review
Developed an AI-assisted retail analytics case study using SQL, Python and Tableau across 1.47M public transactions; improved held-out Precision@8 by 8.5% over a frequency baseline and evaluated promotion response and 432 financial scenarios to frame a selective pilot recommendation.

Do not claim production deployment, measured revenue lift, Metro Market employment or live Tableau validation. The supplied workbook's structural checks passed, but native application opening remains unverified.
