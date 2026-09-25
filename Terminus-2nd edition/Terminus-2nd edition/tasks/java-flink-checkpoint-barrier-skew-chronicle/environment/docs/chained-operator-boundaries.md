# Chained operator boundaries

Some operators include chain_head and chain_tail booleans. When both are true for adjacent chained operators, only the chain_tail operator counts barrier receipts for skew on that chain segment.

When an event operator has chain_head true and chain_tail false, barrier receipts must not also be credited to the next operator in vertex order.

Double counting at chain boundaries inflates barriers_received and collapses skew toward zero.
