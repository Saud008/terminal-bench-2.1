# Ingest snapshot schema

`sysctlmerge ingest` writes an intermediate snapshot JSON before export. `sysctlmerge export` reads that file and must **not** re-parse bundle trees or re-merge fragments from disk.

Path convention: `/app/state/sysctlmerge-snapshot.json` (or any path passed to `--snapshot`).

| Field | Meaning |
|-------|---------|
| `snapshot_version` | Schema version (`1`) |
| `tree_path` | Absolute path to the bundle tree directory |
| `tree` | Bundle directory name (basename of `tree_path`) |
| `seed` | Seed string used for drop-in ordering |
| `processing_order` | Parsed file paths: `main` first, then drop-ins in merge order |
| `effective` | Final sysctl key → string value map after merge |
| `sources` | Winning `file` and 1-based `line` per key |
| `stats` | `keys` (effective count) and `files_processed` (every parsed file including `main`) |

On parse or key errors, `ingest` aborts with exit code `3` and must not write the snapshot or merge-staging files.

Successful `export` validates merge-staging (`validate_merge_staging` exit `4` on missing or mismatched digest), then copies snapshot fields into the apply export documented in `/app/docs/export-schema.md`, adding `apply_version: 1`.

The legacy helper `lexicographic_order` in `/app/lib/staging.sh` is **not** authoritative for merge order; `drop_in_order` in `/app/docs/merge-contract.md` governs drop-in sequencing.
