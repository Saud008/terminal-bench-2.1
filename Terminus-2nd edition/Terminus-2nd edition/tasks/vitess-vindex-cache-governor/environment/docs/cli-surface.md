# CLI surface

vtgatesim ingest --shard-map PATH --vindexes PATH --snapshot PATH [--cache-seed PATH]

Writes /app/state/vindex-snapshot.json per revision-snapshot contract (generation, shard_map_path, vindexes, cache array, coalesce_dropped). Optional --cache-seed loads a JSON array of cache entries before coalesce (see fixture-catalog.md).

vtgatesim route --snapshot PATH --batch PATH --output PATH

Writes route plan JSON with generation, routes (vindex, key, shard, from), cache_hits, scatter_ok.

vtgatesim export --snapshot PATH --plan PATH --audit-out PATH

Writes routing audit per export-schema.md.

vtgatesim migrate --events PATH --snapshot PATH

Applies migration journal to snapshot in place.

Rebuild: go build -mod=readonly -o /usr/local/bin/vtgatesim ./cmd/vtgatesim from /app.
