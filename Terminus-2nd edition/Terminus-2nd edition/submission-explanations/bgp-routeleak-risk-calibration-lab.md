# Submission explanations - bgp-routeleak-risk-calibration-lab

**Task folder:** tasks/bgp-routeleak-risk-calibration-lab/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-16T19:10:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Agents struggle because feature extraction, group holdout, and train-only standardization interact. A partial fix that corrects the sigmoid or Brier score can still leak peer groups or invert private and reserved ASN flags. Threshold tie-breaks and count-weighted ECE add separate traps that only show up when several modules stay wrong together. Hard difficulty comes from needing one coherent calibration pipeline rather than a single-line edit.

## Solution Explanation

The oracle rebuilds the AS-path feature vector with last-hop origin and distinct private versus reserved ranges. It assigns whole peer groups to train, validation, and test roles, then fits standardization means and variances on training rows only. Scoring uses an overflow-safe sigmoid, inclusive F-beta threshold search with a lower-threshold tie-break, and held-out confusion, Brier, and ECE metrics. The run stages an evaluation snapshot before writing the sealed model-card report and audit digest.

## Verification Explanation

The verifier rebuilds the CLI package, then drives evaluate through subprocess against bundled and verifier-only experiments. An independent Python reference recomputes scores, thresholds, and metrics for exact report comparison. Extra contract tests cover feature ranges, group exclusivity, sigmoid stability, scale overrides, and documented exit codes. NOP on the broken baseline scores zero while the oracle patch reaches reward one.
