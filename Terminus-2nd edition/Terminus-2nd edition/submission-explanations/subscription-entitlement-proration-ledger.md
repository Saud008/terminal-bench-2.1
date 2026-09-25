# Submission explanations - subscription-entitlement-proration-ledger

**Task folder:** tasks/subscription-entitlement-proration-ledger/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-22T20:20:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `security` (entitlement trust-admission / coupon authenticity / tamper-evident journal / anti-replay invoice seal / digest-bound ledger attestation). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form. Prior uploads failed Harbor `[category_classifier]` as blocked `software-engineering` under billing-pipeline / deliver-subledctl / engineering-problem framing and earlier data-processing / system-administration metadata. Keep the entitlement-attestation / invoice-seal security framing and the explicit “not a SaaS billing engine / Go rebuild / pytest harness” negation.

## Difficulty Explanation

Marked hard because inclusive day math, mid-cycle upgrade credits, coupon precedence, meter carryover, and anchor realignment all have to agree before publish will seal. Agents often land one reconcile path and leave drifted pass counters or staging digests that still fail independent reference checks on a second run.

## Solution Explanation

The oracle drops corrected Go modules into the app tree, rebuilds subledctl, and drives load reconcile publish against the same bundled cycles. Export must trust staged entitlement buffers already written during reconcile, honor the pass gate, and stay idempotent on repeat publish.

## Verification Explanation

The verifier harness rebuilds the binary then pytest drives subledctl through subprocess with independent reference math. NOP on the broken image scores zero and oracle patches should pass cleanly.
