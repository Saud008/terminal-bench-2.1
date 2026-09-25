# Submission explanations - go-sarif-suppression-baseline-curator

**Task folder:** tasks/go-sarif-suppression-baseline-curator/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-06T03:51:59Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about build a SARIF baseline curator on the working Go tree under /app. I rated it medium because the behavior is split across cli-surface.md, dedupe-collapse.md, delta-export.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and there is at least one decoy source file that looks like the fix target but is not on the hot path. With about 22 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (sarif_curate_run.go, sarif_dedupe_collapse.go, sarif_emitdelta_delta.go, sarif_fingerprint_drift.go) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Re-running on unchanged inputs should produce the same artifacts.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (22 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
