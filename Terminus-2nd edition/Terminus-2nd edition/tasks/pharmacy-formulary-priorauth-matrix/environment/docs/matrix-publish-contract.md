# Matrix publish contract

formulary-matrix.json fields: scenario, as_of, row_count, matrix_digest, rows[].

Each row: plan_id, ndc_normalized, preferred_rxnorm, requires_pa, step_complete, override_applied, effective_rule.

Rows sorted by plan_id ascending then ndc_normalized ascending.

effective_rule is the string baseline when no active override applies for that plan and drug. When an override applies, effective_rule is that winning override's effective_start date string.

matrix_digest is SHA-256 hex of compact digest JSON (no spaces after separators) with keys as_of, row_count, rows, scenario. The rows array in the digest uses the same field set and order as each published row above, already sorted.

publish-matrix requires refresh_revision > 0.
