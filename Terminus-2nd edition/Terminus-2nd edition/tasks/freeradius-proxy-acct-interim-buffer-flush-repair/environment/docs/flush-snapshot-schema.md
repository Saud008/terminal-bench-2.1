# Flush snapshot schema

Path: /app/state/acct-flush-snapshot.json

Top-level fields:

- snapshot_version: integer (1)
- proxy_name: string from config
- home_server: string from config
- sessions: array of session objects sorted by session_start_ts, nas_id, acct_session_id
- flush_queue: array of pending flush entries sorted by session_start_ts then seq
- stats: counter object (see radius-acct-contract.md)

Session object fields: nas_id, acct_session_id, acct_unique_session_id, session_start_ts, interim_interval_sec, input_octets, output_octets, last_interim_ts, status (active or stopped).

Flush entry fields: session_start_ts, seq, acct_status_type, nas_id, acct_session_id.

Export report schema: /app/docs/export-report-schema.md
