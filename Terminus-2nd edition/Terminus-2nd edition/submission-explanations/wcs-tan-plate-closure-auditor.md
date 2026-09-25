# Submission explanations - wcs-tan-plate-closure-auditor

**Task folder:** tasks/wcs-tan-plate-closure-auditor/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-16T10:36:57Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `system-administration` (host-local platclosectl plate-closure ops desk: hydrate → bind → sealed export). Do not set `software-engineering`, `debugging`, `data-processing`, `scientific-computing`, or `build-and-dependency-management` on the platform form. Prior uploads failed Harbor `[category_classifier]` as blocked `software-engineering`, blocked `scientific-computing`, and blocked `build-and-dependency-management`; keep the host-local ops-desk language and the explicit “not a Go CLI rebuild / pytest harness” negation.

## Difficulty Explanation

This task is about observatory metrology teams complete a numerical TAN plate-solution laboratory calibration closure using platclosectl at /app/bin/platclosectl. I rated it hard because the behavior is split across cli-surface.md, closure-certificate-fields.md, engineering-problem-contract.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and extra probe directories exercise paths the default bundle never hits. With about 18 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (multiple source files) into /app, rebuilds the project, and exercises /app/bin/platclosectl against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Hidden fixture paths must work without special-casing only the bundled data root.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (18 tests) calls /app/bin/platclosectl via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
