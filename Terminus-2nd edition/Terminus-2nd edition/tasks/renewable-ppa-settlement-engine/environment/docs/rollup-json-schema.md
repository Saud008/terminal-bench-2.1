# Invoice publish contract

Output path: /app/output/invoice-rollup.json

Schema:

- scenario_id: string
- ppa_id: string
- period_start: YYYY-MM-DD
- period_end: YYYY-MM-DD
- billing_days: integer per holiday-rollup-contract.md
- line_count: count of settlement lines where skipped_curtail is false
- total_amount_cents: sum of amount_cents for non-curtailed lines
- lines_digest: lowercase hex SHA256 of JSON array encoding all settlement lines in sorted row sequence

publish-invoice reads /app/state/settlement-lines.jsonl produced by compile-lines for the same scenario.

Republishing without recompiling must yield identical lines_digest and total_amount_cents when settlement lines are unchanged.
