# Staging snapshot

Ingest writes /app/state/index-staging.json before persisting /app/work/index.json. The snapshot includes doc_count, batch_sha256, deduped index terms from the batch, and written_before_index set true when ordering is correct.
