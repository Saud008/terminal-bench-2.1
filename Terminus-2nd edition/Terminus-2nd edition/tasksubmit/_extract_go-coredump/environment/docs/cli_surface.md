# coreidx authenticity admission surface

Binary path: /app/bin/coreidx

## ingest

```
coreidx ingest --crash-dir DIR --catalog PATH --staging PATH
```

Admits all `.crash.jsonl` evidence files under DIR (sorted by filename), loads the trusted build catalog JSON at PATH, authenticates companion ELF build-IDs under mmap integrity gates, groups duplicate evidence, and writes one tamper-evident JSON object per staged crash line to PATH. The staging PATH may be any writable JSONL file such as /app/state/crash_staging.jsonl or /app/state/alt_staging.jsonl for isolated admission runs.

## export

```
coreidx export --staging PATH --sqlite PATH --summary PATH
```

Reads the on-disk staging chain-of-custody JSONL only, then publishes sealed SQLite attestation per sqlite_export_schema.md and sealed JSON summary with groups and totals.
