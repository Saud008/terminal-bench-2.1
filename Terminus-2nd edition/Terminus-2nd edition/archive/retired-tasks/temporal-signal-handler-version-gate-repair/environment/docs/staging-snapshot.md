# Staging snapshot

Path: `/app/state/signal-snapshot.json`

Fields:

- `workflow_id`, `routed_version`
- `acked_signals` — ordered signal ids accepted this replay
- `staging_written` — must be **false** in the final persisted file (no handler may write the snapshot or set this flag during per-signal processing; see `/app/docs/handler-ack-order.md`)
- `dedup_seen`, `dedup_skipped`
- `heartbeat_offset_ms` — server-relative offsets

Export reads this file; export must not rebuild routing from scratch.
