# Release epoch persistence

Path: `/app/state/release-epoch.json`

```json
{
  "epoch": 1
}
```

## Rules

- Each `reconcile` invocation must bump `epoch` by one before writing release staging.
- The file persists across reconciles until `/app/scripts/reset-state.sh` clears it.
- First reconcile after reset starts at epoch `1`.
- `release_epoch` in `/app/state/release-staging.json` and in the export report must equal the bumped epoch file value.
- Do not derive `release_epoch` from `ledger_tail_sequence` or `next_sequence`. Ledger sequence resets on every reconcile; the epoch does not.
