# Submission explanations - rust-sbom-vex-impact-reachability-atlas

**Task folder:** tasks/rust-sbom-vex-impact-reachability-atlas/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-03T10:09:56Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about task identity d3d9fa1946 anchors the VEX supply-chain contract for this release-gate atlas. I rated it hard because the behavior is split across expiry-windows.md, exposure-ledger-schema.md, package-normalization.md and lib.rs. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and replay counters and commit files have to stay in sync across two CLI runs. With about 38 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (reachvex_impact_emit.rs, reachvex_norm_purl.rs, reachvex_runtime_reach.rs, reachvex_stage_digest.rs) into /app, rebuilds the project, and exercises /app/bin/vexatlas against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. A second run on unchanged inputs should stay idempotent. Export must respect the replay counter rules.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (38 tests) calls /app/bin/vexatlas via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
