# Submission explanations - go-vault-token-lease-renewal-risk-auditor

**Task folder:** tasks/go-vault-token-lease-renewal-risk-auditor/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-25

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Marked hard because each renewal depends on earlier rows of the same token and on the parent granted expiry so a one module patch never closes the suite.Partial progress that only tightens static caps still fails when lifetime budget,depth ordered delegation,or cycle classification stays wrong.

## Solution Explanation

The oracle overlays corrected Go modules under the app tree,rebuilds vaultaud,and runs audit then rollup on the same fixtures agents see.The key insight is to resolve parents before children using lineage depth and to honor policy override stops while folding lifetime budget into granted ttl.

## Verification Explanation

Pytest rebuilds the binary then drives the CLI through subprocess and compares full staging plus rollup output to independent reference math.Hidden transcript dirs exercise override plus depth order and cycle score clamp so a bundled only fix cannot pass.
