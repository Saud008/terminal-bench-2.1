# Connector budget ledger

Lookup pair_loss_db by connector type from inventory.
Sum connector losses for attributed junctions plus measured splice losses per segment.
A segment is accepted when total_loss_db is at most planned splice loss for that segment plus connector budget on its boundaries.
