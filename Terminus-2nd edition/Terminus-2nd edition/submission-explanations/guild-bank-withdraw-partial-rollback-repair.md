# Submission explanations - guild-bank-withdraw-partial-rollback-repair

**Task folder:** tasks/guild-bank-withdraw-partial-rollback-repair/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-09T10:39:28Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

The guild bank operational daemon at /usr/local/bin/guildbankd manages guild treasury gold, vault item stacks, withdrawals, transfer-out, audit export, and nightly interest accrual with. I rated it hard because the behavior is split across audit-order.md, bank-contract.md, bound-items.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are replay counters and commit files have to stay in sync across two CLI runs. With about 13 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (multiple source files) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. The fix keeps parsing, core logic, and export aligned with the schemas named in the instruction. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. A second run on unchanged inputs should stay idempotent. Export must respect the replay counter rules.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (13 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Tests mutate paths and inputs enough that hard-coded outputs fail even if one fixture passes. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
