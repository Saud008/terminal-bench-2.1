# Reuse timer forecast publish

Command:

```
rdampctl emit-reuse-forecast --scenario SCENARIO --out PATH [--root DIR]
```

Requires run_id greater than zero and an existing flap ledger from drive-feed.

Writes JSONL at PATH. Each retained ledger slot yields one object with these keys in this field sequence when serialized:

- peer_id
- prefix
- penalty_now
- reuse_threshold
- half_life_ms
- ms_to_reuse
- forecast_anchor_ms
- slot_digest

## Slot retention

Emit a forecast line only when the slot is currently suppressed or peak_penalty is at least reuse_threshold. Quiet advertised routes with peak_penalty below reuse_threshold are omitted.

## ms_to_reuse

When penalty_now is already below reuse_threshold, ms_to_reuse is 0.

Otherwise find the smallest non-negative integer delta_ms such that:

floor(penalty_now * half_life_ms / (half_life_ms + delta_ms)) is strictly less than reuse_threshold.

Use integer arithmetic only. When half_life_ms is 0, emit an error and do not write the file.

## forecast_anchor_ms

Use the slot last_ts_ms from the flap ledger as forecast_anchor_ms. Do not substitute wall clock or the maximum event-time across peers.

## slot_digest

Lowercase hex SHA-256 of the UTF-8 string:

peer_id|prefix|penalty_now|reuse_threshold|ms_to_reuse|forecast_anchor_ms

Separated by ASCII pipe characters with no spaces.

## Line order

Sort lines by peer_id ascending, then prefix ascending, same as the suppression atlas.
