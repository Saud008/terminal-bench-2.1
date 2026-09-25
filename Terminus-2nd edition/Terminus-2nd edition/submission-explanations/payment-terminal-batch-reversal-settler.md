# Submission explanations - payment-terminal-batch-reversal-settler

**Task folder:** tasks/payment-terminal-batch-reversal-settler/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-19T16:00:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about acquiring-bank settlement operators delivering termsetctl to compile trusted payment-terminal batch journals and sealed HMAC settlement bundles. I rated it hard because the behavior is split across batch-journal-contract.md, reversal-pairing-contract.md, cutoff-window-contract.md, seal-hmac-contract.md and multiple Go modules. Fixing one layer often looks fine on the bundled scenarios while other checks still fail. The painful parts are linkage-key pairing must ignore transcript array and event_ms order between a sale and its reversal, while journal emission still sorts by event_ms, and the witness must HMAC the journal_digest rather than the bundle body. With about 20 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (oracle_cutoff.go, oracle_journal.go, oracle_reversal.go, oracle_seal.go, and related modules) into /app, rebuilds the project, and exercises /app/bin/termsetctl against the same public fixtures agents see. Compile normalizes rows, pairs by terminal/auth/links_sale_id/amount without a timestamp guard, applies inclusive cutoff, then sorts for journal emission. Key insight: follow the doc contracts for pairing eligibility versus journal order, digests, and HMAC message bytes instead of patching around symptoms in one module. A second run on unchanged inputs should stay idempotent.

## Verification Explanation

test.sh stages verifier-only fixtures from tests/ into /opt at verify time, rebuilds the binary, then runs pytest. Pytest calls /app/bin/termsetctl via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert journal staging and seal fields before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
