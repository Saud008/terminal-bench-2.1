# spend atlas layout

publish-spend-atlas requires amendment_pass greater than zero. It does not accept --scenario; export reads staged balances and rejections from the portfolio already stored in /app/state/grant-portfolio.db. The analytical rollup JSON fields are grant_balances, rejections, atlas_digest, amendment_pass. grant_balances lists spent_cents and remaining_cents per grant_id sorted lexicographically.

`rejections` is always a JSON array of `{expense_id, reason}` objects. When no expenses were rejected, serialize an empty array `[]`. Never emit `null`, omit the key, or substitute another sentinel for an empty rejection list. The same empty-array rule applies to `grant_balances` when no grant rows are present.
