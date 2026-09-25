# Platform rubric — bgp-routeleak-risk-calibration-lab

**Task folder:** tasks/bgp-routeleak-risk-calibration-lab/
**Written:** 2026-07-16T18:25:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent builds the ordered BGP AS-path vector with last-hop origin, distinct private and reserved ASN ranges, relationship features, and first-hop customer semantics, +3
Agent assigns whole peer groups to sorted train/validation/test roles and fits population standardization statistics on training rows only, +3
Agent applies the configured feature scale, scores through an overflow-safe sigmoid, and chooses inclusive F-beta=1.5 thresholds with the lower-threshold tie-break, +3
Agent reports held-out confusion counts, squared Brier, count-weighted 10-bin ECE, and an input-order audit digest, +3
Agent stages the evaluation snapshot before sealing the requested model-card report, +3
Agent honors TB3_FEATURE_SCALE and produces valid reports for both bundled and verifier-only experiments, +2
Agent rebuilds routeleaklab after changing evaluation modules and preserves the CLI's documented exit codes, +2
Agent leaves protected docs, fixtures, configuration, and decoy telemetry unchanged, +1
Agent patches only a metric while feature extraction, split assignment, or audit ordering remains incorrect, -3
Agent uses row-index holdout or all-row standardization so validation scores leak training groups, -3
Agent hardcodes fixture reports or edits verifier tests or hidden fixtures, -5
