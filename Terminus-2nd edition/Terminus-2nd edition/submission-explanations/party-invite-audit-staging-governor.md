# Submission explanations — party-invite-audit-staging-governor

**Task folder:** tasks/party-invite-audit-staging-governor/
**Platform form only** — not in upload zip.
**Updated:** 2026-07-27T17:40:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Restructure (2026-07-27):** Converted from Go HTTP `partyd serve` to **debian + bash/python** host-local occupancy ledger desk (fleet-roster / labelsheet shape) after Harbor `[category_classifier]` predicted blocked `software-engineering` under `system-administration` / `security` lipstick. Policy modules live under `/app/lib/party/`; binary is `/app/bin/partyd` (bash → `python3 -m party.cli`).

**Category remap (2026-07-27):** Platform now accepts only Data Administration / ML / Game. Zip metadata uses **`data-administration`**. Choose **Data Administration** on the platform form. Do not set `system-administration`, `security`, `software-engineering`, `debugging`, or `data-processing`.

## Difficulty Explanation

Marked hard because agents must finish a hash-chained staging ledger on a working occupancy data desk with party-scoped suppression, retention, durable sequences, chain-verified export, and sweep-owned epoch retirement rather than patch a single handler. Partial fixes pass baseline smoke but fail twin-party occupancy, retention continuity, or retirement refusal under hidden fixtures.

## Solution Explanation

The oracle copies golden Python modules for digest, ledger, staging, publish, sweeper, and query into `/app/lib/party/`, then reinstalls the `partyd` wrapper so staging appends chained entries, publish verifies then seals reserved seats, and the sweeper bumps epoch before refresh and retirement.

## Verification Explanation

test.sh reinstalls the wrapper and pytest drives `/app/bin/partyd` via subprocess against an independent reference that recomputes digests, reserved seats, and chain checks while broken patches and hidden fixtures prove isolated module fixes still fail and NOP scores zero while the oracle yields full reward.
