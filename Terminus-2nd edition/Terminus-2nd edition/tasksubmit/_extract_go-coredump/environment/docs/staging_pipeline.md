# Authenticity admission and sealed attestation pipeline

## Ingest (admission)

```
coreidx ingest --crash-dir <DIR> --catalog /app/fixtures/catalog/build_index.json --staging /app/state/crash_staging.jsonl
```

Staging lines must be sorted by `timestamp` ascending, then `crash_id` ascending.

Each staged object contains: crash_id, timestamp, signal, pid, group_key, build_id (uppercase hex), top_symbol, frames (array of authenticity-resolved frame rows).

## Export (sealed attestation)

```
coreidx export --staging /app/state/crash_staging.jsonl --sqlite /app/output/crash_index.sqlite --summary /app/output/crash_summary.json
```

SQLite receives tables `crash_groups` and `crash_frames` per sqlite_export_schema.md.

Summary JSON contains `groups` (sorted by group_key) and `totals.group_count`.

## Verifier fixture override

When the verifier sets `TB3_CRASH_DIR` to an alternate directory, ingest must read `.crash.jsonl` files from that path instead of the bundled fixtures directory.

## Verifier reference helpers

Pytest imports `coreidx_verifier_lib` for independent staging math, uses the standard library `sqlite3` module to read `/app/output/crash_index.sqlite`, and uses `hashlib.sha256` to pin bundled catalog bytes before invoking coreidx.
