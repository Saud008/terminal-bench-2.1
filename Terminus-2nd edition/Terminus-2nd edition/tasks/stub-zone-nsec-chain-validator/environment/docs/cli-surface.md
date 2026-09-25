# CLI surface

Binary: /usr/local/bin/nsecval (build from /app/cmd/nsecval).

## ingest

nsecval ingest --capture PATH --snapshot PATH

Reads one capture JSON, writes chain-snapshot.json at snapshot path with zone, soa_serial, record_count, records. Exits 0 on success.

## validate

nsecval validate --capture PATH --report PATH [--snapshot PATH]

Default snapshot path is /app/state/chain-snapshot.json. Runs ingest snapshot write, NSEC chain check, query walk, report at PATH with keys zone, soa_serial, chain_valid, queries, cache_hits, snapshot_sha256.

TB3_CAPTURE_DIR when set to an absolute directory replaces /app/fixtures/captures/ for default bundled capture paths in tests only; explicit --capture flags are unchanged.
