# Engineering problem contract

Static analysis SARIF reports describe findings with tool name, rule identifier, URI location, severity, and partial fingerprint strings. Suppression policies define time-bounded acceptance windows keyed by canonical rule identity and URI prefix. A baseline snapshot records the last accepted finding set for a repository. The sarbctl curator reconciles a new scan against policy and baseline, then publishes a finding delta that classifies each row as new, removed, drift, suppressed, or unchanged.

## Finding identity chain

Canonical rule keys combine normalized tool and rule_id after alias resolution and version suffix stripping. URI paths pass through remap rules before deduplication, suppression matching, and drift comparison. Duplicate SARIF rows that share rule key, remapped URI, and start line collapse to the highest severity finding. Physical fingerprint hashes bind rule key to remapped location; drift compares partial fingerprint strings against the baseline row at the same location key.

## Suppression reconciliation failures

A finding matches a suppress_until row when canonical rule_key and remapped URI prefix align. Active suppression requires observed_at on or before the policy until instant in the policy timezone. Findings observed after until must land only in rejected-findings.jsonl with reason suppression_expired. They must not appear in baseline-revision curated entries or in finding-delta.json export rows. Mis-ordered canonicalization or remap lets suppressions attach to the wrong SARIF rows.

## Baseline delta failures

Delta export compares curated entries against baseline snapshot rows keyed by finding_id and location identity. Category precedence is drift over suppressed over unchanged; new and removed rows stand alone. emit must refuse when reconcile_revision is zero, when scan_revision disagrees between staging and baseline snapshot, or when findings_digest on staging does not match recomputation from staged findings.

## Scan artifact integrity

finding-staging.json must record absolute paths to policy and remap inputs, content digests for SARIF and policy bytes, and findings_digest built from sorted compact JSON lines per finding-staging.md. staging-seq.json tracks monotonic scan_revision across repeated scans. reconcile-revision.json records the curate generation used by emit.

## Non-authoritative code paths

The repository may contain legacy merge helpers that predate the scan-curate-emit split. Only sarbctl subcommands documented in cli-surface.md produce authoritative staging, reconcile, and delta artifacts.
