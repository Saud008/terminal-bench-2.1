# Submission explanations - bson-objectid-clock-skew-duplicate-guard

**Task folder:** tasks/bson-objectid-clock-skew-duplicate-guard/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-16T06:55:53Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about task identity 6d8396ec10 defines the engineering problem for bson objectid clock skew duplicate guard. I rated it hard because the behavior is split across digest-hex-seal.md, engineering-problem-contract.md, intake-batch.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and extra probe directories exercise paths the default bundle never hits. With about 19 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (oracle_digestseal.go, oracle_intakegate.go, oracle_jsonlresume.go, oracle_objclock.go) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Hidden fixture paths must work without special-casing only the bundled data root.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (19 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
