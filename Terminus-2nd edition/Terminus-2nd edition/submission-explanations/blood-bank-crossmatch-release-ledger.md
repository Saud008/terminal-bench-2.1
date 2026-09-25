# Submission explanations — blood-bank-crossmatch-release-ledger

**Task folder:** tasks/blood-bank-crossmatch-release-ledger/
**Platform form only** — not in upload zip.
**Updated:** 2026-07-10T10:30:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Agents must align ABO and Rh rules, antibody exclusion, expiry windows, emergency waiver audit, and SQLite release persistence across seven Go modules and eight docs. Fixing Rh typing alone still leaves antibody load, repeat seal growth, or override authorizer gaps. Hidden traps and second-run idempotency checks punish one-file patches that pass bundled scenarios.

## Solution Explanation

The oracle patches hemcompat, immuno, shelflife, emergaudit, matrixstage, and sealpublish modules, then rebuilds bbreleasectl. Screening must complete before seal-releases writes the ledger. Repeat seal on the same scenario must keep ledger_digest stable without duplicating rows.

## Verification Explanation

test.sh rebuilds Go sources before pytest. Tests invoke bbreleasectl via subprocess and compare SQLite, matrix JSONL, and release-ledger.json to crossmatch_spec math. Hidden fixtures under /opt/verifier-fixtures cover antibody and override traps beyond bundled data.
