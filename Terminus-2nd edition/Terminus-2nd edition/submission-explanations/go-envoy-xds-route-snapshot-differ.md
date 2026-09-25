# Submission explanations - go-envoy-xds-route-snapshot-differ

**Task folder:** tasks/go-envoy-xds-route-snapshot-differ/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-03T06:30:48Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about mesh operators promoting Envoy control-plane revisions need an offline differ that compares paired xDS JSON snapshots without a live management server. I rated it hard because the behavior is split across cli-surface.md, cluster-weight-contract.md, diff-export-contract.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and replay counters and commit files have to stay in sync across two CLI runs. With about 18 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (emit_chg.go, persist_stage.go, pick_tier.go, ref_bind.go) into /app, rebuilds the project, and exercises /app/bin/xsnapctl against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. A second run on unchanged inputs should stay idempotent. Export must respect the replay counter rules.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (18 tests) calls /app/bin/xsnapctl via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
