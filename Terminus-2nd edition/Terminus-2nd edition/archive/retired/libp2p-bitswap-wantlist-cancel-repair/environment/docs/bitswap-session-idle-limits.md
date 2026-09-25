# Session idle timeout

Default idle limit is 5000 ms cumulative tick idle_ms. When LastActivity reaches the limit, wants_remaining clears and partial block buffers must also clear. In-flight counters zero out after idle flush.

Tick events do not credit ledger. Activity from want, merge_wants, cancel, block_start, block_part, or block_done resets LastActivity to zero.
