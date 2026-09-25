# Ingest staging snapshot

Every successful index command writes /app/state/index-staging.json before persisting /app/work/index.json. The snapshot JSON contains keys doc_count, batch_sha256 (hex SHA-256 of the raw batch bytes), terms (sorted unique collapsed terms from the batch), and written_before_index (boolean true when the snapshot is emitted before the live index file is updated). The live index update must not occur when staging write fails.
