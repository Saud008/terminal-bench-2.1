# Replay ledger

Every successful `build_snapshot` appends one JSON line to `/app/state/sysctlmerge.replay.jsonl`. `publish_export` must validate the ledger before writing apply export JSON.

## Record schema

Each append is one compact JSON object per line:

| Field | Meaning |
|-------|---------|
| `tree` | Bundle directory name from the snapshot |
| `seed` | Seed string from the snapshot |
| `snapshot_digest` | Same digest as merge-staging (`canonical_snapshot_digest` per `/app/docs/digest-contract.md`) |
| `files_processed` | Snapshot `stats.files_processed` |
| `layer_keys_digest` | Lowercase hex `SHA-256` of canonical JSON for `layer_keys` from the sibling merge-staging file (`sort_keys=true`, compact separators) |

`append_replay_record(snapshot_path)` reads the snapshot and merge-staging, then appends the record.

## Validation

`validate_replay_record(snapshot_path)` scans the ledger for the **last** record matching `(tree, seed)` from the snapshot. Exit `0` when that record's `snapshot_digest`, `files_processed`, and `layer_keys_digest` match the snapshot and its merge-staging artifact. Exit `5` when the ledger is missing, no matching record exists, or any field mismatches.

Export must call `verify_export_ready` from `/app/lib/guard.sh` after ingest completes and before writing `--output`. Guard runs merge-staging validation then replay validation. On failure, exit `5` (or `4` from staging) and do not write the export file.

## apply_digest

Successful apply export JSON includes `apply_digest`: lowercase hex `SHA-256` over the same canonical payload used for `snapshot_digest` (`processing_order`, `effective`, `sources` with `sort_keys=true`, compact separators).
