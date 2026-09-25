# Submission explanations - hitbox-hurtbox-frame-alignment-replay-engine

**Task folder:** tasks/hitbox-hurtbox-frame-alignment-replay-engine/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-03T15:05:13Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

The combat tools team needs a sealed tick-ledger replay export workflow on the Rust hitreplay workspace under /app. I rated it medium because the behavior is split across collision-report-schema.md, frame-index.md, hit-event-dedup.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and extra probe directories exercise paths the default bundle never hits. With about 20 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (golden_collision.rs, golden_export.rs, golden_frame.rs, golden_hurtbox.rs) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Hidden fixture paths must work without special-casing only the bundled data root.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (20 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
