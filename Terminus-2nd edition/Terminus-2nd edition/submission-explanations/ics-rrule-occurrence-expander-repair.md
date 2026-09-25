# Submission explanations - ics-rrule-occurrence-expander-repair

**Task folder:** tasks/ics-rrule-occurrence-expander-repair/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-03T09:50:03Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

The expand CLI at /app/cmd/expand reads iCalendar fixtures and writes expanded occurrence rows into SQLite. I rated it hard because the behavior is split across fixture-catalog.md, ical-expansion-contract.md, README.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are there is at least one decoy source file that looks like the fix target but is not on the hot path. With about 19 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (multiple source files) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. The fix keeps parsing, core logic, and export aligned with the schemas named in the instruction. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Re-running on unchanged inputs should produce the same artifacts.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (19 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Tests mutate paths and inputs enough that hard-coded outputs fail even if one fixture passes. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
