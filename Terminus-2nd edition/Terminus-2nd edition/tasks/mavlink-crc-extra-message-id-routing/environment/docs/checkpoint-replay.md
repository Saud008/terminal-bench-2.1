# Checkpoint replay

`mavctl decode` may persist accepted frames to a SQLite checkpoint and resume across runs.

## Flags

- `--checkpoint PATH` — append newly accepted frames after session filter and dedup.
- `--resume` — load prior accepted frames for the same `--seed` from `PATH` before merging export.

## Pipeline order

1. Extract frames from input bytes.
2. Permute extracted frames with the seed (see `/app/docs/mavlink-contract.md`).
3. Validate CRC and known `msg_id` catalog.
4. Session sequence guard per `(sysid, compid)` — drop stale rollbacks, allow u8 wrap-forward. On `--resume`, seed the guard from checkpoint rows for the active `--seed` before filtering newly validated frames from the current input.
5. Dedup against checkpoint ledger (when resuming) and the current run.
6. Append newly accepted frames to checkpoint when `--checkpoint` is set.
7. Write `/app/state/decode.snapshot.json` with merged accepted frames, run counters, and resume fact diffs (`/app/docs/export-schema.md`).
8. Publish export from the decode snapshot only — do not re-parse input bytes during export.

## Resume fact diffs

On `--resume`, compute `diff_rows` by comparing decoded facts from newly accepted frames against checkpoint baseline facts for the active `--seed`. Each changed fact must record both `old_value` and `new_value` as stringified JSON scalars per `/app/docs/export-schema.md`.

## Sequence guard

Track the last accepted `seq` independently for each `(sysid, compid)` pair. Sharing sequence state across component IDs on the same system ID is incorrect. A new frame is a **stale rollback** when `last.wrapping_sub(new)` is in `1..127`. Otherwise accept and update `last`.

## Dedup key

`(sysid, compid, msg_id, seq)` — duplicates in the checkpoint ledger or current run are skipped and counted in `deduped_count`.

## Checkpoint scope

The dedup ledger and resume load are scoped to the active `--seed`. Other seeds stored in the same database must not affect the current run.
