# Export summary

Export JSON schema version 1:

- schema: 1
- account: string
- reference_epoch: integer
- maxage_sec: integer
- tz_offset: integer
- dry_run: boolean
- synced_messages: integer count of manifest rows selected
- synced_bytes: integer sum of size_bytes for selected rows (not the message count)
- folders: sorted list of folder names contributing at least one selected message
- cutoff_utc: integer cutoff used for the run

Dry-run exports still write the export JSON but must not create or modify /app/state/sync-run.json and must not mutate sync-ledger.db.

synced_bytes must equal the arithmetic sum of size_bytes; using synced_messages as synced_bytes is incorrect.

## sync-run.json

Path: /app/state/sync-run.json

Written only after a non-dry-run sync (step 6 in spec.md). Schema version 1 fields:

- schema: integer 1
- account: string from imap-meta
- reference_epoch: integer epoch seconds passed to sync (must match the export JSON for the same run)
- synced_messages: integer count of manifest rows selected (must match the export JSON for the same run)
- synced_bytes: integer sum of size_bytes for selected rows (must match the export JSON `synced_bytes`)
- dry_run: boolean, always `false` when this file is written
