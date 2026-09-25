# Merge staging artifact

`build_snapshot` writes a sibling merge-staging JSON next to every successful ingest snapshot. `publish_export` must validate that file before writing apply export JSON.

## Path convention

For snapshot path `/app/state/sysctlmerge-snapshot.json`, staging is `/app/state/sysctlmerge-snapshot.merge-staging.json` (same directory, snapshot basename + `.merge-staging.json`).

`staging_path_for(snapshot_path)` in `/app/lib/staging.sh` returns that path on stdout.

## Staging schema (`staging_version: 1`)

| Field | Meaning |
|-------|---------|
| `staging_version` | Schema version (`1`) |
| `snapshot_digest` | Lowercase hex digest from `canonical_snapshot_digest` in `/app/docs/digest-contract.md` |
| `layer_keys` | Ordered list of `{ "file": <relative path>, "keys": [<keys declared in that fragment>] }` following `processing_order` |
| `last_file` | Final path in `processing_order` |

`write_merge_staging(snapshot_path)` reads the snapshot, computes `snapshot_digest` by calling `canonical_snapshot_digest` from `/app/lib/digest.sh` (never `/app/lib/bind.sh` or inline digest math), and writes the staging file.

`validate_merge_staging(snapshot_path)` loads the staging file, recomputes the digest from the snapshot, and returns shell exit code `0` when they match. Return `4` when the staging file is missing or the digest mismatches.

## Export gate

`publish_export` must call `verify_export_ready` from `/app/lib/guard.sh` (see `/app/docs/export-guard-contract.md`) before copying snapshot fields into the apply export. On validation failure, propagate exit `4` or `5` and do not write `--output`.

`lexicographic_order` remains a **non-authoritative** legacy helper; never use it for merge order.
