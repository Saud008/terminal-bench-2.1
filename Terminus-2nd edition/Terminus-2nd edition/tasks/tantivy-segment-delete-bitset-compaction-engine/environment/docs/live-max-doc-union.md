# Live max doc union

live_max_doc in segment-stats.json is the exclusive upper bound on allocated global doc ids after concatenating segment doc spaces in ingest order.

Compute it as the sum of max_doc across all staged segments. It is not the maximum single-segment max_doc field and it is not the count of non-deleted documents.
