# Index pipeline — host-local segment-commit control plane

This task is a **system-administration** host-local tantool index-ops control plane. Operators admit JSONL segment batches into a catalog, enforce merge publish and WAL barriers, and publish sealed hit-list exports from committed state only. The working baseline under /app must keep admission gates, publish barriers, and sealed export aligned; it is not a generic service repair exercise.

tantool maintains per-index catalogs under /app/state/index-catalog.json. Each ingest call appends one staging segment from a JSONL batch. Merge combines all staging segments into one on-disk segment, updates the reader registry, and records pending live doc counts. Commit runs the WAL barrier, freezes committed_live_docs, and writes /app/state/index-snapshot.json.

Search and stats read committed segments only. Staging segments are invisible to search until merge and commit complete.
