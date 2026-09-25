# Partition staging snapshot

Path: /app/state/frozen-segment-snapshot.json

Fields: engine, topic, scenario, segment_count, record_count, records[], staging_digest.

staging_digest is SHA-256 hex of canonical JSON object with keys topic, scenario, records sorted as stored after load.

Each staged record includes canonical_key computed at ingest per key-normalize-contract.md.
