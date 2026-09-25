# Ingest → export pipeline

`chparts read` runs decode (ingest) then export. See `/app/docs/merge-snapshot.md` for staging and `/app/docs/export-schema.md` for report output.

## Commands

```text
chparts ingest --parts-dir DIR --config /app/config/table.json --db /app/data/parts.db
chparts export --output /app/output/parts-report.json
chparts read    --parts-dir DIR --config /app/config/table.json --db /app/data/parts.db --output /app/output/parts-report.json
```

## Stage 1 — ingest

0. Call staging.WriteEarlyManifest at ingest start to write /app/state/parts.manifest with table_suffix, table_name, and an empty rows list (rows omitted or []). Export must not read this file; the manifest is a scratch artifact that must not influence export output.
1. Walk part bundle directories under `--parts-dir`.
2. Register part metadata, validate checksums, load rows, merge by primary key using the version column, apply TTL pruning **after** merge completes, finalize commit barrier, write `/app/state/parts-snapshot.json`.
3. Skip parts whose `batch_id:part_id` idempotency key was already ingested.

If any part fails checksum validation, ingest and read must abort with a non-zero exit status per /app/docs/part-bundle-format.md.

Ingest must not publish export JSON.

## Stage 2 — export

1. Read `/app/state/parts-snapshot.json` only.
2. Write `--output` per `/app/docs/export-schema.md`.

Export must not re-walk `--parts-dir` or query SQLite row payloads.

## Module map

| Module | Stage | Role |
|--------|-------|------|
| `ingest/register.go` | ingest | Part registration + checksum commit |
| `ingest/idempotency.go` | ingest | Replay keys |
| `merge/comparator.go` | ingest | Primary-key merge |
| `ttl/drop.go` | ingest | TTL pruning after merge |
| `commit/barrier.go` | ingest | fsync barrier + max_block |
| `staging/snapshot.go` | ingest | Snapshot persistence + early manifest scratch file |

Refactors must keep Go symbol names and signatures listed in /app/docs/go-module-api.md.
| `export/publish.go` | export | Report publish from snapshot |
