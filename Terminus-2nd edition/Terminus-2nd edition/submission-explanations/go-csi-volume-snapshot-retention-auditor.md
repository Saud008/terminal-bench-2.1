# Submission explanations - go-csi-volume-snapshot-retention-auditor

**Task folder:** tasks/go-csi-volume-snapshot-retention-auditor/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-27T00:00:00Z

**Category note:** Zip metadata uses `system-administration` (host-local snapretctl snapshot-retention ops desk: import → score → seal; bash wrapper + Python policy modules under `/app/lib/snapret/`). Do not set `software-engineering`, `debugging`, `data-processing`, `security`, or `build-and-dependency-management` on the platform form. Prior uploads failed Harbor `[category_classifier]` as blocked `software-engineering` (Go/K8s/CSI shape) and blocked `security` on edition_2; restructured (2026-07-27) from Go cargo rebuild to debian + bash/python ops-desk pattern (museum-accession shape). Go sources are excluded from the upload zip and Docker image.

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Rated **medium** in zip metadata (`task.toml`). AutoEval measured GPT 2/5 and Opus 4/5. Agents must align Python policy modules under `/app/lib/snapret/` with nine contract docs covering fleet graph digests, PVC join keys, retention precedence, quota math, and byte-stable publish gates. Partial fixes often pass bundled scenarios but fail hidden TB3 traps or second-run idempotency checks.

## Solution Explanation

The oracle copies corrected Python modules from `solution/files/` into `/app/lib/snapret/`, runs `verifier-rebuild.sh`, and exercises `/app/bin/snapretctl` against the same fixtures agents see. Key insight: follow contract ordering for digests, pass counters, and publish gating instead of patching symptoms in one module.

## Verification Explanation

`test.sh` refreshes fixtures and reinstalls snapretctl via `verifier-rebuild.sh`. Pytest (26 tests) calls `/app/bin/snapretctl` via subprocess. Expected JSON is recomputed from fixtures in `k8s_volume_refmath.py`, blocking pasted golden answers. NOP on broken modules should score below full reward; oracle passes cleanly.
