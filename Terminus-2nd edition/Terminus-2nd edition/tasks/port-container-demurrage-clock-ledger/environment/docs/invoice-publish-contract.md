# Invoice publish contract

publish-invoices publishes carrier demurrage invoice lines from staged_dwell rows.

## Gate

publish-invoices requires clock_pass greater than zero in /app/state/clock-pass.json. Attempts when clock_pass is zero must fail with non-zero exit status.

## Output path

/app/output/demurrage-invoices.json

## JSON shape

| Field | Meaning |
|-------|---------|
| engine | demurctl |
| clock_pass | current pass count |
| invoice_digest | eight-hex digest over lines and grand total |
| grand_total_cents | sum of line total_cents |
| lines | per-container invoice rows |

Each line includes container_id, total_cents, currency, tier1_days, tier2_days, tier3_days, and active_hold when applicable.
