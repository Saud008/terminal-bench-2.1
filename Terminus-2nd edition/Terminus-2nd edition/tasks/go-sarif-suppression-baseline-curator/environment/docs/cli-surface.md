# CLI surface

Command: /usr/local/bin/sarbctl

Subcommands:

| Subcommand | Purpose |
|------------|---------|
| scan | Parse SARIF, write finding-staging.json and bump staging-seq.json |
| curate | Apply policy and baseline, write reconcile-revision.json and rejected-findings.jsonl |
| emit | Validate staging digest, write finding-delta.json |
| run | scan then curate then emit with the same flags |

## scan flags

--sarif absolute path to SARIF JSON
--policy absolute path to suppression policy JSON
--remap absolute path to path remap JSON
--baseline absolute path to baseline snapshot JSON

## run flags

Same four flags as scan.

## Output paths

| Artifact | Path |
|----------|------|
| finding-staging.json | /app/state/finding-staging.json |
| staging-seq.json | /app/state/staging-seq.json |
| reconcile-revision.json | /app/state/reconcile-revision.json |
| rejected-findings.jsonl | /app/output/rejected-findings.jsonl |
| finding-delta.json | /app/output/finding-delta.json |

When TB3_FIXTURE_DIR is set to an absolute directory, bundled scan, policy, remap, and baseline basenames resolve only under that directory.
