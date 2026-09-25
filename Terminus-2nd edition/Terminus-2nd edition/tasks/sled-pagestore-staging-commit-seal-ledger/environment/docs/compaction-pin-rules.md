Compaction removes unreachable page ids from /app/state/page_registry.json

Pages listed in any /app/state/pins/{table}-{snapshot_id}.json pinned_pages set must never be reclaimed while the pin file exists.
