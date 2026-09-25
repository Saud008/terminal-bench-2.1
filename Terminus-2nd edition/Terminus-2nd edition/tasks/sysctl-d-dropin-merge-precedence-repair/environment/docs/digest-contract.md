# Snapshot digest contract

Merge-staging, replay-ledger, and apply export share one canonical digest for snapshot binding.

## Module

`/app/lib/digest.sh` exports `canonical_snapshot_digest SNAPSHOT_PATH`, which prints a lowercase hex `SHA-256` digest to stdout.

## Payload

Read the snapshot JSON at `SNAPSHOT_PATH`. Canonicalize a JSON object with exactly these keys:

| Key | Source |
|-----|--------|
| `processing_order` | snapshot field |
| `effective` | snapshot field |
| `sources` | snapshot field |

Serialize with `sort_keys=true` and compact separators `,` and `:`. Hash the UTF-8 bytes.

## Consumers

| Caller | Usage |
|--------|-------|
| `write_merge_staging` | stores result as `snapshot_digest` |
| `validate_merge_staging` | recomputes and compares |
| `append_replay_record` | stores result as `snapshot_digest` |
| `validate_replay_record` | recomputes and compares |
| `publish_export` | stores result as `apply_digest` |

All consumers must call `canonical_snapshot_digest`; do not duplicate digest math inline and do not substitute `/app/lib/bind.sh` legacy helpers (see `/app/docs/legacy-bindings.md`).
