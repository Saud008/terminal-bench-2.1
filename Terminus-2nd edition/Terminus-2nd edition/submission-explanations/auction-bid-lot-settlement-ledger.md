# Submission explanations - auction-bid-lot-settlement-ledger

**Task folder:** tasks/auction-bid-lot-settlement-ledger/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-19T15:10:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `security` (settlement integrity / deposit trust gates / ledger attestation). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form.

## Difficulty Explanation

Agents must wire a three-stage Go CLI that admits auction scenarios into SQLite under reserve and tie trust gates, then seals buyer invoices with deposits and premiums applied. The hard part is that mistakes in catalog load, lot verdict, or settlement emit layers interact. A fix on one stage can look correct on bundled scenarios while hidden traps still fail on tie precedence, negative adjustments, or idempotent republish. Cross-run checks also require adjudication_pass and ledger_digest to stay stable when inputs do not change.

## Solution Explanation

The oracle replaces the broken lot verdict, scenario load, and settlement emit sources, normalizes line endings, rebuilds auctctl, and runs the same CLI path agents use. The main insight is to treat contracts in the docs as the source of truth for reserve floors, tie precedence, adjustment sign, and publish guards rather than patching symptoms in one file. Deposit netting and premium tiers must stay consistent through the full pipeline.

## Verification Explanation

test.sh rebuilds the Go binary before pytest. Tests invoke auctctl through subprocess and compare outputs to an independent Python reference model. Bundled scenarios cover the main settlement path while hidden fixture directories probe tie and adjustment traps that a catalog-only fix cannot satisfy. sqlite3 checks read awards_buffer rows before publish, and hashlib recomputes ledger_digest to block pasted answers.
