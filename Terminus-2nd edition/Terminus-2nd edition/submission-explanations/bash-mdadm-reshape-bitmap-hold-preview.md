# Submission explanations - bash-mdadm-reshape-bitmap-hold-preview

**Task folder:** tasks/bash-mdadm-reshape-bitmap-hold-preview/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-16T13:10:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation


This task asks agents to implement mdreshape so fleets can preview which mdadm arrays are safe to reshape before a grow window. I rated it hard because bitmap freezes, spare holds, degraded floors, illegal RAID hops, and hour budgets are split across many docs and modules. Fixing one policy often looks fine on the bundled scenario while other cases still fail. Ranking and atlas sealing must stay aligned with the reshape ledger across a second run. With about 27 checks, a partial fix usually collapses once criticality order or multi-spare holds are exercised.

## Solution Explanation


The oracle copies corrected modules under /app/internal/raidops, rebuilds the CLI, and runs scan/compile/publish against the same fixtures agents see. Each policy is repaired to match its contract rather than patching symptoms in the ledger stage alone. The important insight is that publish must seal the atlas from the on-disk reshape ledger, and salted array names must survive load_seq advances. Bitmap clear planning and multi-spare hold checks have to follow the fleet inventory fields exactly as the docs define them.

## Verification Explanation


tests/test.sh rebuilds mdreshape and runs pytest with reward.txt. About 27 subprocess tests compare CLI JSON to independent mdreshape_reference.py rather than golden blobs. Persistence suites fail shallow one-module patches. NOP on the broken baseline scores 0. the oracle path scores 1.
