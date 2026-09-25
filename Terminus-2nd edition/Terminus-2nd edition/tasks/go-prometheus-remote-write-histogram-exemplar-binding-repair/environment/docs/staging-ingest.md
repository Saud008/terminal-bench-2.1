# Staging ingest files

Each successful write persists one JSON record at /app/data/ingest/SEED.json where SEED matches the request seed field.

Record shape:

```json
{"seed":"SEED","sequence":N,"series":[...]}
```

Sequence starts at 1 for the first accepted write after reset and increments by 1 on every later accepted write for the same seed without reset. Snapshot export must read the latest on-disk record for the seed and include the sequence value in the exported JSON under the top-level sequence field.

Write handling must only decode and persist staging records. Relabel deduplication and exemplar binding run during snapshot export, not during write handling.

Histogram schema values from decode must be stored unchanged in the staging record. Do not downgrade native histogram schema before writing staging files.
