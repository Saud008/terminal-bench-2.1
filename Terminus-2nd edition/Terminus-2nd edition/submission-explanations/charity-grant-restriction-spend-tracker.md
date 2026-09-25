# Submission explanations - charity-grant-restriction-spend-tracker

**Task folder:** tasks/charity-grant-restriction-spend-tracker/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-20T02:10:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Revision note:** Clarified that only load-portfolio takes --scenario; apply-amendments and publish-spend-atlas use the portfolio already stored in grant-portfolio.db.Prior wording in grantctl-verbs.md made every verb sound scenario-flagged and both agents failed after fixing real bugs by requiring that flag on apply/publish.

## Difficulty Explanation

Marked hard because overlap precedence,temporal amendment windows,category allow lists,alias resolution,and empty array atlas serialization all have to hold before publish will seal.Agents often land one amendment path and leave drifted pass counters or null rejections that still fail independent reference checks on a second run.

## Solution Explanation

The oracle drops corrected Go modules into the app tree,rebuilds grantctl,and drives load apply publish against the same bundled portfolios.Export must trust staged balances and rejections already written during apply,keep rejections as an empty JSON array when nothing was rejected,and stay idempotent on repeat publish.

## Verification Explanation

The verifier harness stages verify time fixture overlays then rebuilds the binary before pytest drives grantctl through subprocess with independent reference math.NOP on the broken image scores zero and oracle patches should pass cleanly.
