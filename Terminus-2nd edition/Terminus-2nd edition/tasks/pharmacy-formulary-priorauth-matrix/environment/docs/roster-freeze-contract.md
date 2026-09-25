# Formulary roster freeze snapshot

Path: /app/state/formulary-roster.json

Fields: engine, scenario, as_of, drugs, plans, overrides, step_chains, roster_digest.

roster_digest is SHA-256 hex of compact digest JSON (no spaces after separators; equivalent to encoding/json.Marshal or json.dumps with separators=(",", ":")) with keys as_of, drugs, overrides, plans, scenario, step_chains.

Before hashing, reorder only the drugs array by normalized NDC ascending (apply /app/docs/ndc-normalize-contract.md to each drug ndc for the sort key). Drug objects in the digest keep their original raw ndc strings from the fixture; do not rewrite ndc fields to normalized form for the digest payload. Leave overrides, plans, and step_chains in fixture order; do not sort those arrays for the digest.
