# Settlement integrity contract — auction-bid-lot-settlement-ledger

**Task folder:** tasks/auction-bid-lot-settlement-ledger/

## Objective

Deliver a post-auction settlement integrity CLI that admits bids under reserve_floor and tie_precedence trust gates, applies tiered buyer_premium and bidder deposit_netting caps, honors withdrawn_lot flags and signed post_sale_adjustments, and seals buyer invoices backed by a tamper-evident SQLite ledger attestation.

## Verifier contract

Independent Python reference (auction_refmath) recomputes awards and invoice lines from fixture JSON. Pytest drives auctctl load-catalog, adjudicate-lots, and publish-invoices via subprocess and compares SQLite awards_buffer plus /app/output/buyer-invoices.json.

## Distinct failure modes

Reserve floor off-by-one, tie_precedence ignoring bid_ts or bidder_id, awarding withdrawn lots, stripping negative adjustments, deposit double-apply on republish, publish-only fixes that skip awards_buffer rows.
