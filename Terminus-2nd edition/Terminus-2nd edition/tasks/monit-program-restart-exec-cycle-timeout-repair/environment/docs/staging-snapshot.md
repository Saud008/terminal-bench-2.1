# Staging snapshot

ingest copies config and scenario metadata into /app/state/cycle-snapshot.json:

- program name string
- stop_timeout_sec, start_delay_sec, restart_limit integers
- scenario name basename
- event_count integer
- snapshot_sha256 hex sha256 of scenario file bytes

replay must echo snapshot_sha256 in replay-report.json when ingest ran in the same reset window; otherwise recompute from scenario bytes.
