# Platform rubric — go-sarif-suppression-baseline-curator

**Task folder:** tasks/go-sarif-suppression-baseline-curator/

Agent implements scan staging that writes findings_digest per finding-staging.md sorted line serialization, +3
Agent persists absolute policy_path and remap_path on finding-staging.json during scan, +2
Agent applies rule canonicalization with alias and version suffix stripping before dedupe, +3
Agent remaps URIs with longest prefix_strip and rewrite before collapse and drift keys, +2
Agent collapses duplicate findings by severity rank error warning note with finding_id tie break, +2
Agent flags fingerprint drift when baseline row shares location but partial fingerprint differs, +3
Agent rejects expired suppress_until findings to rejected-findings.jsonl with suppression_expired reason, +2
Agent bumps reconcile_revision only after curate completes and emit refuses when it is zero, +2
Agent classifies delta rows with drift beating suppressed beating unchanged per delta-export.md, +3
Agent patches only internal/merge decoy while leaving scan or emit hot path broken, -3
Agent skips path remap before dedupe so duplicate keys split across CI and workspace prefixes, -3
Agent writes findings_digest without trailing newline per finding line in digest body, -2
Agent emits finding-delta before reconcile_revision is positive, -2
Agent hard-codes delta_digest pending placeholder instead of canonical sorted JSON hash, -3
