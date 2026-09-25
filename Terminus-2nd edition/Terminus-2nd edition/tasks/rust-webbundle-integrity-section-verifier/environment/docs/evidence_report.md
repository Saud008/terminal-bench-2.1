# Evidence report schema

Output path: /app/output/bundle_attestation_report.json

Top-level keys:

- bundles: array of per-bundle evidence objects
- totals: aggregate counters

Each bundle entry contains bundle_id, exchanges array, and findings array.

Finding kinds: hash_mismatch, scope_violation, ctype_violation, duplicate_resolved.

Totals fields:

- exchange_count: staged exchange rows across all bundles
- verified_count: rows where hash_ok and in_scope and ctype_ok
- finding_count: sum of hash_failures + scope_violations + ctype_violations
- hash_failures, scope_violations, ctype_violations: separate counters

Bundles sort by bundle_id ascending. Exchanges within a bundle sort by canonical_url.

Idempotency checks may write scratch staging files such as /app/state/alt_staging.jsonl or /app/state/iso_staging.jsonl and scratch reports such as /app/output/alt_report.json or /app/output/iso_report.json before comparing byte-identical reruns of the primary export paths.
