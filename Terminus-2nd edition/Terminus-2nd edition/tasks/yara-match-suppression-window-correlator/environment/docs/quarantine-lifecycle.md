# Quarantine lifecycle

quarantine_states rows track sample_sha256 per asset_id.

Active quarantine suppresses matching events when:

- state is active
- detected_ms >= entered_ms
- cleared_ms is zero or detected_ms is strictly less than cleared_ms

Released quarantine (state released with cleared_ms set) does not suppress events at detected_ms greater than or equal to cleared_ms.

Suppressed incidents set suppression_reason quarantine_active.
