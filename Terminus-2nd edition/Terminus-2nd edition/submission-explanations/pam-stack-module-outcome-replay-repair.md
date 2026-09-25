# Submission explanations — pam-stack-module-outcome-replay-repair

**Task folder:** tasks/pam-stack-module-outcome-replay-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

Agents must repair the pamreplay Bash CLI so nineteen catalog stacks under /app/fixtures/stacks/ replay correctly through nine interacting library modules. Contracts in twelve files under /app/docs/ split responsibilities across stack flattening, PAM control semantics, per-phase environment commit and rollback, global audit sequencing, staging and outcome snapshots, guard validation, and export that must not re-run modules. Partial fixes are common: correcting requisite halt in runner.sh still fails when export reads live stubs instead of the outcome snapshot, or when outcome_guard accepts a forced zero exit code. Include depth, nested fragments, sufficient-before-required ordering, optional traps, and cross-run staging merge poison bundled and hidden fixtures that are not obvious from a single broken file.

## Solution Explanation

The oracle copies nine golden Bash modules from solution into /app/lib/, normalizes line endings, and runs reset-state.sh. stack.sh and compose.sh flatten includes and preserve entry order. runner.sh executes phases and modules with correct requisite, required, sufficient, and optional behavior. environment.sh commits pam_env changes per phase rules and rolls back on failure before audit is written. audit.sh assigns one global seq counter across the whole replay. staging.sh writes /app/work/replay.staging.json, outcome.sh builds the outcome snapshot, outcome_guard.sh validates it, and export.sh emits JSON plus the audit sidecar from that snapshot only. The CLI exits non-zero when the replay fails even if an export path was requested.

## Verification Explanation

Pytest runs sixty-eight behavioral cases after test.sh invokes verifier-rebuild.sh and reset-state.sh. Each catalog stack is replayed through subprocess calls to /app/bin/pamreplay with per-run seed tokens, and results are compared to reference_replay.py, an independent Python reimplementation that does not import /app/lib/. Tests assert exit codes, export JSON, audit jsonl sidecars, staging and outcome artifacts, export-only mode, idempotent byte stability, and partial-golden traps that fail when only one module is patched. Hidden stacks under tests/hidden_fixtures/ cover order-sensitive sufficient ordering and optional-sufficient traps not present in the bundled catalog. Oracle reward is one only when every test passes.
