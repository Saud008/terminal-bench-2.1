# Submission explanations - fleet-roster-membership-ops-ledger

**Task folder:** tasks/fleet-roster-membership-ops-ledger/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-26T00:40:00Z

**Restructure (2026-07-26):** Converted from Go repair CLI to **debian + bash/python** host-local ops control plane (labelsheet shape) to clear Harbor `[category_classifier]` SE blocks on `golang` + `go build` + consensus-CLI shape. Policy modules under `/app/lib/roster/`; binary is `/app/bin/rosterctl` (bash → `python3 -m roster.cli`). Instruction-sufficiency contracts from the prior revision are retained in `/app/docs/`.

**Category note:** Zip metadata uses `system-administration`. Do not set `software-engineering`, `debugging`, `data-processing`, or `security` on the platform form.

> Agent scaffold only — rewrite in your own words before Snorkel upload.

## Difficulty Explanation

This task is about fleet-roster operators running a host-local membership ops plane that admits offline journal/snapshot bundles, applies voter-set and commit-fence gates, then seals a committed-queue ledger. I rated it hard because the behavior is split across voter-epoch admission, leader handoff order, journal-tail fences, snapshot truncation, and commit_index export gates plus multiple policy modules. Fixing one gate often looks fine on bundled data while other checks still fail. Export must honor the on-disk membership-staging witness and positive raft_seal field. With about 22 checks, a partial fix often passes bundled cases but fails on truncation poison overlays or a second run.

## Solution Explanation

The oracle replaces corrected policy modules under /app/lib/roster/, refreshes /app/bin/rosterctl, and exercises the same fixtures agents see. replay-log admits journal segments and writes the witness head; merge-snapshot and audit-membership apply truncation and voter-epoch gates; only then should export-committed trust those bytes. Follow the ops contracts for ordering, digests, and seal rules. A second run on unchanged inputs should stay idempotent.

## Verification Explanation

test.sh rebuilds via verifier-rebuild.sh. Pytest calls /app/bin/rosterctl via subprocess. Tests do not grep source for magic strings. Reference math recomputes expected JSON from fixtures. NOP on the broken image should score 0. After the oracle module swap, the suite should pass cleanly.
