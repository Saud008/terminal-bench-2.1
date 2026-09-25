Milestone 1 heartbeat, timeout, and query behavior must stay correct. Decision tasks are still lost when the sticky partition map goes stale, and history shard cursors jump on duplicate event_id per /app/docs/sticky-partition-map.md and /app/docs/history-shard-reader.md.

Repair /app/internal/sticky and /app/internal/history so workers poll the live sticky generation at decision_poll_ms and duplicate history events increment duplicate_events_skipped without advancing history_cursor_seq by raw event_id. Full merged scenarios in /app/docs/fixture-catalog.md including 06-merged-stall.json must replay cleanly.

Rebuild cadence-replay after Go edits. Verifier-only sticky rotation scenarios may appear under /opt/verifier-fixtures/. Do not edit /app/docs/ or /app/fixtures/.
