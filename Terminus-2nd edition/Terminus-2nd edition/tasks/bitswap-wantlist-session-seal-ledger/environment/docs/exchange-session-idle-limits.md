# Session idle timeout

Default idle limit is 5000 ms cumulative tick idle_ms. When LastActivity reaches the limit, idle flush must clear both partial block buffers and the corresponding wants_remaining entries. In-flight counters zero out after idle flush.

Tick events do not credit ledger. Activity from want, merge_wants, cancel, block_start, block_part, or block_done resets LastActivity to zero.
