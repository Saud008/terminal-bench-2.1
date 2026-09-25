# Submission explanations - go-temporal-workflow-history-compaction-inspector

**Task folder:** tasks/go-temporal-workflow-history-compaction-inspector/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-19T20:30:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Category note

Zip metadata uses `system-administration` (host-local workflow-history ops curator: staging → compaction seal → SQLite/replay-ledger publish). If the platform form still offers `data-processing` or `build-and-dependency-management`, leave the form blank or match the zip — do not set `software-engineering` or `debugging`.

## Difficulty Explanation

This task operates wfhistctl as an offline history compaction curator. I rated it hard because the behavior is split across activity-attempt-contract.md, can-boundary-contract.md, cli-surface.md and multiple source files. Getting one stage correct often looks fine on the bundled fixtures while later emit-inspect or seal-gate checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs, and replay counters and seal files have to stay in sync across two CLI runs. With about 21 checks in the suite, a partial implementation often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (chronorder_rank.go, dbmirror_write.go, eventcache_persist.go, genfold_seal.go) into /app, rebuilds the project, and exercises /app/bin/wfhistctl against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. A second run on unchanged inputs should stay idempotent. Export must respect the replay counter rules.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (21 tests) calls /app/bin/wfhistctl via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
