# Atlas emission

Path: /app/output/redaction-risk-atlas.json

Top-level fields: scenario, finding_count, findings[], atlas_digest.

Each finding object includes finding_id (sort key), party_id (linked party when alias graph matched), exhibit_ref (normalized exhibit label such as Exhibit 12-A), docket (primary docket number from scenario docket set), page (int), line (1-based line within page), term (sealed term token matched), risk_score (float).

Findings sorted by finding_id ascending.

emit-atlas requires index_revision > 0 in /app/state/index-revision.json.

atlas_digest is SHA-256 hex of compact JSON with keys finding_count, findings, scenario.
