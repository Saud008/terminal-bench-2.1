# Engineering problem contract

fsplatlas aligns OTDR power traces with planned splice mileposts and route segment intervals.
Acceptance depends on detected loss events, milepost bracket binding, connector budget reconciliation, and duplicate ranking by epoch precedence.
Partial fixes that only adjust detection without segment ledger reconciliation or budget debits fail hidden verifier cases.
Agents must prove per-segment loss totals by ranking events and reconciling inventory debits using the doc contracts, not a single-file patch.
