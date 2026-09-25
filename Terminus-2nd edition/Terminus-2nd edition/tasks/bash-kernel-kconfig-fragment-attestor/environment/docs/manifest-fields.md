# Manifest fields and digests

emit-manifest output JSON fields:

run_id, symbols, policy_violations, totals, manifest_digest.

Each symbols row has name, value, and source_layer. Values are y, m, or n.

manifest_digest is sha256 of JSON array of objects with name, value, and source_layer sorted by name.

symbols array must be sorted by name ascending.

Re-export with the same run id after reset-state must yield identical manifest_digest when stage content is unchanged. Output manifests use paths such as /app/output/run-alpha-manifest.json for bundled runs.

manifest_queries in bundle.json list symbols tests assert in output rows.

Digest helpers in /app/tools/kcfg_primitives.py use Python hashlib for SHA256 over sorted JSON payloads.

Violation codes match /app/docs/policy-constraints.md.
