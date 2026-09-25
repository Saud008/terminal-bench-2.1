# Vector clock contract

Lamport vector clocks govern causal ordering for chat events. This contract is independent of execution ledger replay semantics.

## Merge

Component-wise maximum across all keys present in either map. Missing keys count as zero.

## Increment

Before recording a sender event, increment that sender component by one on the merged frontier, then merge the event supplied vector_clock map.

## Happens-before

Clock A happens-before B when every component of A is less than or equal to the corresponding component of B and at least one component is strictly less.

## Concurrent

Neither happens-before the other.

## Causal sort tie-break

Sort events for timeline emission by causal order. When two events are concurrent, break ties by event_id ascending lexicographic order.

## Shard load order

Shard files match shard_NNN.jsonl where NNN is a decimal integer. Sort by numeric NNN ascending, not lexicographic string order.
