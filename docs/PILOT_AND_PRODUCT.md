# Product and pilot brief

## Product proposal
At the start of shopping or list preparation, show a short list of optional replenishment reminders. The implemented evaluation corresponds to the beginning of an observed shopping day. Before deploying at home ahead of a visit, define the forecast horizon and reevaluate; the current model does not predict visit timing.

The shortlist should offer confirm, dismiss and already-have-it actions. Abstain when evidence is weak. Do not show raw model probabilities as certain inventory estimates. Use product names only after joining the retailer's own catalog; the public dataset provides limited product descriptions.

## Evidence and commercial constraints
The selected model provides a statistically supported but modest gain in exact-product ranking. The confidence-filtered policy improves precision while serving fewer days. Neither demonstrates customer convenience or extra purchases. The central modeled contribution is negative, so a pilot requires a low learning cost or an explicitly valued convenience objective, not an assumed sales windfall.

## Proposed test
Randomize eligible households, not individual product recommendations, into: existing experience; reminders only; identical reminders plus a predefined offer policy. Keep assignments stable, and stratify on history-based frequency and spending. Use a catalog/availability join and suppress unavailable products before showing suggestions.

Primary commercial measure: net contribution per assigned eligible household over a fixed horizon. Secondary measures: list-building time, perceived usefulness, reminder acceptance, opt-outs, trip frequency and net quantity over subsequent cycles. Distinguish assignment, exposure, click, list addition, purchase and redemption events. Include nonusers in intention-to-treat estimates.

Choose a minimum worthwhile effect and perform power calculations with retailer-specific baseline variance and household clustering. Cover multiple normal purchase cycles and a post-offer period. Review concurrent campaigns, stockouts and cross-arm spillover. Prespecify stopping rules and subgroup interpretation. No actual experiment was run in this project.

## Deployment outline if evidence supports it
Batch ingest daily transaction/catalog feeds; validate keys and discount definitions; build as-of features from prior purchases; score only eligible candidates; join current availability; apply confidence policy; serve a short list. Log exposure and actions, then reconcile to later purchases. Version the feature logic, model, threshold and experiment assignment.

Monitor missing catalog joins, candidate coverage, score drift, category calibration, weekly ranking quality, latency, dismissals, opt-outs and net contribution. A fallback can use the frequency rule or abstain when history is sparse. A new household needs a separately designed cold-start experience.

Production integrations, inventory feed, app interface, live serving, access control and experiment event instrumentation are designs here; no production system has been deployed.
