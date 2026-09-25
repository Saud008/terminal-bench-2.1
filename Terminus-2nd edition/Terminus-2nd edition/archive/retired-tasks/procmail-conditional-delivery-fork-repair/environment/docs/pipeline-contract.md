# Pipeline contract

## simulate

1. Load suite meta, rc, and mbox from `--suite`.
2. Apply SET lines and suite defaults to the delivery environment.
3. For each message in order, walk the recipe tree per rc-format.md, lock-scope.md, delivery-flags.md, and fork-orgmail.md.
4. Write `/app/state/delivery-snapshot.json` (or `--snapshot` path) with:

```json
{
  "snapshot_version": 1,
  "suite_id": "...",
  "environment": {"HOST": "...", "HOSTNAME": "...", "ORGMAIL": "..."},
  "deliveries": [
    {"message_id": "...", "mbox": "...", "recipe_id": "...", "reason": "match"}
  ],
  "skipped_recipes": [
    {"recipe_id": "...", "reason": "lock_busy"}
  ],
  "stats": {
    "messages_total": 0,
    "recipes_evaluated": 0,
    "recipes_skipped": 0,
    "deliveries_count": 0,
    "lock_serializations": 0,
    "orgmail_fallbacks": 0,
    "duplicate_suppressed": 0
  }
}
```

Delivery `reason` is `match` for normal targets or `orgmail_fork_fallback` for ORGMAIL.

`pipeline.sh` calls `deliver_record` once per successful recipe with a mbox target. The `c` flag continues sibling recipe evaluation only; it does not authorize a second `deliver_record` call for the same recipe row (see delivery-flags.md).

`stats.duplicate_suppressed` is maintained by `deliver.sh`: it increments only when `deliver_record` blocks an append because the `(message_id, mbox, recipe_id)` triple already exists in `deliveries`. See delivery-flags.md.

## audit

Read the snapshot path from `--snapshot` and write audit-export-schema.md JSON to `--output`. Do not re-read mbox or rc.
