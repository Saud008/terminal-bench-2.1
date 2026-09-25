# tie-break-contract

When two bids share the highest hammer for a lot, the earlier bid_ts wins. If bid_ts ties, lower bid_seq wins. If bid_seq ties, lexicographically lower bidder_id wins. This tie_precedence chain is independent of deposit_netting.
