# Submission explanations - ecs-archetype-table-migration-journal-repair

**Task folder:** tasks/ecs-archetype-table-migration-journal-repair/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-08T11:54:55Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

The archectl CLI at /app replays ECS-style migration journals and runs component queries against fixture worlds under /app/fixtures/worlds/. I rated it hard because the behavior is split across archetype-hash.md, component-registration.md, ecs-contract.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and extra probe directories exercise paths the default bundle never hits. With about 38 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (module-manifest.json, targets-journal.txt, targets-publish.txt, targets-runner.txt) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Hidden fixture paths must work without special-casing only the bundled data root.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (38 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
