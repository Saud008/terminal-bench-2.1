# Stable republish

Report JSON uses stable JSON field order from encoding/json MarshalIndent.

A second publish-audit without state mutation must produce byte-identical volsnap-audit-report.json and orphan-snapshot-ledger.jsonl.
