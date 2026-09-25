# Platform rubric — auction-bid-lot-settlement-ledger

**Task folder:** tasks/auction-bid-lot-settlement-ledger/

Agent loads catalog rows into /app/state/settlement.db via load-catalog, +3
Agent adjudicates awards with reserve floor greater than or equal to reserve_cents, +3
Agent breaks bid ties using bid_ts then bid_seq then bidder_id ordering, +3
Agent marks withdrawn lots as withdrawn without buyer invoice rows, +3
Agent applies tiered buyer premium rate_bps with cap from lot premium_tier, +3
Agent nets bidder deposits against invoice subtotal without exceeding remaining deposit, +3
Agent preserves signed negative post-sale adjustment_cents on invoices, +3
Agent increments adjudication_pass in /app/state/adjudication-pass.json on adjudicate-lots, +2
Agent blocks publish-invoices until adjudication_pass is positive, +2
Agent publishes sorted buyer invoices at /app/output/buyer-invoices.json with ledger_digest, +2
Agent republishes idempotently without double-applying deposits on same pass, +2
Agent rebuilds auctctl via verifier-rebuild.sh before subprocess CLI checks, +2
Agent awards lot when hammer equals reserve using strict greater than only, -3
Agent picks higher bidder_id when bid_ts differs on tied hammer amounts, -3
Agent awards withdrawn lots when bids exceed reserve, -3
Agent strips negative adjustments to absolute values during catalog load, -3
Agent double-applies deposit on second publish-invoices without ledger guard, -3
