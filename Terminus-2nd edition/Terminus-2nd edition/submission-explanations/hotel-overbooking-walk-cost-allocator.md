# Submission explanations - hotel-overbooking-walk-cost-allocator

**Task folder:** tasks/hotel-overbooking-walk-cost-allocator/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-10T01:20:06Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about when sellable room inventory falls short of confirmed demand, revenue analysts need a walk-cost financial planner that reconciles reservation demand with room inventory, transforms blackout. I rated it hard because the behavior is split across capacity-snapshot-contract.md, cli-surface.md, demand-score-contract.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and replay counters and commit files have to stay in sync across two CLI runs. With about 22 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (patch_atlas_emit.go, patch_atlas_prep.go, patch_cal_blackout.go, patch_cal_span.go) into /app, rebuilds the project, and exercises /app/bin/overbookctl against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. A second run on unchanged inputs should stay idempotent. Export must respect the replay counter rules.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (22 tests) calls /app/bin/overbookctl via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
