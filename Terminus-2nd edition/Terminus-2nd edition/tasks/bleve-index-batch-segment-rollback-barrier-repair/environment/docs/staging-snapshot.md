# Staging Snapshot

Every ingest attempt must update the batch snapshot at /app/state/batch-snapshot.json during ingest flow.

Snapshot schema:
- index: string
- batch_path: string
- record_count: integer
- status: one of open, committed, rolled_back

The snapshot is used for operational diagnostics and must be written during ingest flow.
