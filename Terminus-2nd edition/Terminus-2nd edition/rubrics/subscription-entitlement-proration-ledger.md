# Platform rubric — subscription-entitlement-proration-ledger

**Task folder:** tasks/subscription-entitlement-proration-ledger/

Agent ingests cycle fixtures into /app/state/billing.db via ingest-cycle, +3
Agent computes inclusive entitlement segment day counts for proration base cents, +3
Agent credits unused old-plan value on mid-cycle upgrade per proration-segment-contract, +3
Agent applies exclusive coupon precedence before stackable fixed discounts, +3
Agent carries unused included units into post-downgrade segment overage math, +3
Agent realigns entitlement window end when anchor_shift effective within segment, +3
Agent writes entitlement-staging.json with compact staging_digest over segments, +3
Agent increments reconcile_pass in /app/state/reconcile-pass.json on reconcile, +2
Agent blocks export-invoices until reconcile_pass is positive, +2
Agent publishes sorted subscription-invoices.json with ledger_digest at /app/output, +2
Agent republishes idempotently with stable ledger_digest on stable-republish, +2
Agent rebuilds subledctl via verifier-rebuild.sh before subprocess CLI checks, +2
Agent uses exclusive day count omitting final cycle day for proration windows, -3
Agent double-applies all coupons including exclusive and stackable together, -3
Agent ignores usage carryover after downgrade plan_change events, -3
Agent exports invoices before reconcile-entitlements completes successfully, -3
Agent leaves anchor_shift rows without truncating entitlement window end date, -3
Agent hashes staging_digest from pretty-printed JSON instead of compact segments, -3
