# Hit event deduplication

During sampling, an attacker may register multiple raw overlaps against the same defender instance on one tick (for example repeated bone queries). Before appending hits to a tick ledger row, collapse duplicates that share the same logical contact key:

```
(tick, attacker_id, defender_id, instance_id)
```

Keep the first hit for each key and discard later rows with the same tuple on that tick. Dedup runs during the sampling stage, not during export aggregation.

Export must preserve the per-tick hit lists stored in the ledger; it must not re-run collision or re-deduplicate.
