# Landing ledger JSONL

Path: /app/var/quota-ledger-{token}.jsonl with header /app/var/quota-ledger-{token}.header.json

Each emit pass writes ledger files under /app/var/.

Each JSONL line is one harvest landing row: landing_id, vessel_id, species_raw, species_resolved, product_weight_kg, live_weight_kg, landed_at, accepted, reject_reason.

Header fields: run_token, season, row_count, ledger_fingerprint.

run_token equals the fqrctl --token value for that emit pass (for example tok-hdr in bundled header contract tests).

ledger_fingerprint is sha256 hex of JSON with row_count, run_token, season only.

Lines sorted by landing_id before write.
