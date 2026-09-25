# Merge contract

Each bundle tree contains `manifest.json` with:

- `main`: path to the base `sysctl.conf` relative to the tree root
- `drop_ins`: ordered list of `sysctl.d` fragment paths relative to the tree root

## Two-stage pipeline

1. **`ingest`** — `build_snapshot(tree, seed, snapshot_path)` parses and merges fragments, writes the snapshot per `/app/docs/snapshot-schema.md`, then `write_merge_staging` per `/app/docs/merge-staging.md`, then `append_replay_record` per `/app/docs/replay-ledger.md`.
2. **`export`** — `publish_export(snapshot_path, output_path)` validates merge-staging and the replay ledger, reads the snapshot only, and writes the final apply JSON per `/app/docs/export-schema.md`.

`sysctlmerge apply` chains ingest then export. Export must not re-parse bundle files or re-run merge logic from disk.

## Library modules

Repair logic lives in `/app/lib/*.sh`. The CLI sources these modules and calls their exported functions **by name** — do not rename entrypoints.

`build_snapshot` subprocesses helpers that source `/app/lib/parse.sh`, `/app/lib/order.sh`, `/app/lib/layers.sh`, and `/app/lib/digest.sh`. Drop-in ordering for ingest is **`compute_drop_in_order` in `order.sh` only** — not `drop_in_order` in `tree.sh` (legacy helper, not on the ingest hot path). Fragment accumulation is **`merge_fragment_into_state` in `layers.sh`**. Shared digest binding is **`canonical_snapshot_digest` in `digest.sh`** — staging, replay, and export must call it rather than inlining hash math.

`lexicographic_order` in `staging.sh` is a **non-authoritative** legacy helper — do not use it for merge order.

## Processing order

1. Parse `main` first.
2. Parse each drop-in in the order returned by `drop_in_order(tree, seed)`.

`drop_in_order` must **not** sort filenames lexicographically and must **not** use Fisher-Yates shuffle or other PRNG permutations.

Deterministic order: sort `drop_ins` by ascending hexadecimal `SHA-256` digest of a UTF-8 seed-and-path string. The digest input format and separator are defined in `/app/docs/sysctl-format.md` (ordering section). Use manifest paths exactly as written (for example `sysctl.d/drop-03.conf`).

`stats.files_processed` must count every parsed file in `processing_order`, including `main`.

Different seeds therefore reorder the same fragment list and can change which drop-in wins key collisions.

Later assignments **override** earlier keys for the same name. Override is per-key: processing a fragment replaces only the keys it declares; keys from earlier files that the fragment does not mention remain in the effective map. When the same key appears on multiple lines within one fragment, the **last** line in that file wins for both `effective` and `sources`.

## Precedence

When the same key appears in `main` and a drop-in, the drop-in wins because it is processed later. Among drop-ins, the last file in `drop_in_order` wins for colliding keys.

## Failure policy

Any invalid key or malformed assignment line aborts ingest/apply with exit code `3` and no snapshot or output file write, even when earlier files in `processing_order` parsed successfully. The CLI must surface that exit code to the caller.
