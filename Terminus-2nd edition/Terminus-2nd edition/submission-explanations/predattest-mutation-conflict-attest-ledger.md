# Submission explanations - predattest-mutation-conflict-attest-ledger

**Task folder:** tasks/predattest-mutation-conflict-attest-ledger/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-16T23:51:07Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about fleet operators watch graph-fleet cutover windows where some mutation-wave commits get held with a labeled reason and others get admitted. I rated it hard because the behavior is split across conflict-precedence-hold.md, cutover-rollout-ops.md, deny-pin-hold.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and there is at least one decoy source file that looks like the fix target but is not on the hot path. With about 25 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (multiple source files) into /app, rebuilds the project, and exercises /app/bin/wavehold against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Re-running on unchanged inputs should produce the same artifacts.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest calls /app/bin/wavehold via subprocess. Tests do not grep source for magic strings. Reference math lives under /tests/wavehold_math.py (not /opt) so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Run-state, custom --output, and exact exit-code-2 CLI probes cover missing scan/compile sequencing. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
