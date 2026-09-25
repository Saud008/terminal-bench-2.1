# Export guard contract

`publish_export` must not write apply JSON until merge-staging and replay-ledger alignment checks pass.

## Module

`/app/lib/guard.sh` defines:

| Function | Role |
|----------|------|
| `verify_export_ready SNAPSHOT` | Runs `validate_merge_staging` then `validate_replay_record`; propagates exit `4` or `5` |
| `cmd_verify_snapshot SNAPSHOT` | Prints `{"aligned":true}` or `{"aligned":false}`; exit `0` when aligned, `1` when not |

Digest math stays in `staging.sh` and `replay.sh`. Guard orchestrates cross-artifact checks only.

## CLI

```
sysctlmerge verify --snapshot PATH
```

Reloads the snapshot, its merge-staging sibling, and the replay ledger tail for `(tree, seed)`. Exit `0` when aligned, `1` when misaligned.

## Export gate

`publish_export` in `/app/lib/export.sh` must call `verify_export_ready` before emitting `--output`. Do not inline staging or replay validation in `export.sh`.
