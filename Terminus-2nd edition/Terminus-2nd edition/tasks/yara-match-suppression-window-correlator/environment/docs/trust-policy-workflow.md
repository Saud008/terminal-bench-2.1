# SOC trust policy workflow

yaracor implements an offline security correlator for YARA detections. Operators load SOC policy manifests and scan events, stage a witness snapshot on disk, evaluate trust policy gates in a fixed order, then seal an incident bundle for downstream attestation.

## Trust gates (correlate order)

1. Rule revision window — event rule_revision must be active at detected_ms per rule-revisions.md.
2. Suppression ticket — matching ticket suppresses actionable status per suppression-windows.md.
3. Sample hash dedupe — first-seen sample_sha256 per asset wins per hash-dedupe.md.
4. Criticality escalation — asset tier may escalate at detected_ms per criticality-escalation.md.
5. Quarantine lifecycle — active quarantine suppresses matching samples per quarantine-lifecycle.md.

Events failing the rule revision gate are appended to rejected-events.jsonl. Remaining events proceed to export after correlate_generation increments.

## Witness and seal fields

Staging carries events_digest, policy_sha256, and policy_path witnesses binding staged events to the loaded policy manifest. Export recomputes events_digest and refuses tampered staging. events_digest uses the fixed event field order in event-staging.md. The sealed bundle includes bundle_digest over a recursively normalized payload (sorted object keys and float-to-int coercion at every nesting depth) per incident-bundle-export.md.

## Policy resolution

Correlate prefers the absolute `policy_path` recorded in staging when that file still exists. If `policy_path` is empty or missing on disk, correlate resolves policy JSON by matching `policy_sha256` under `/app/fixtures` or `YARACOR_FIXTURE_DIR` when set (candidates `policy/policy-east.json` then `policy.json`). Off-catalog and parametrized ingest paths outside the fixture root require the `policy_path` fallback; see event-staging.md.
