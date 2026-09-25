# Rollup snapshot

Path: /app/state/rollup-snapshot.json

Fields:

- generated_at_ms (int) ingest completion time in UTC epoch milliseconds
- series (array) one object per built rollup window and tier

Each series row includes metric, optional labels, tier, window_start_ms, window_end_ms, and tier-specific value fields.

Series must sort by metric, then window_start_ms, then tier.

Staleness markers on raw tier rows must propagate to every downsample tier listed in config for the same metric and window.
