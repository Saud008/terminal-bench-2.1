# Sync transaction order

`mailsync sync` must keep the database and maildir consistent when flag letters change.

## Required order

1. Begin SQLite transaction.
2. Upsert all message rows and sync metadata.
3. **COMMIT** the transaction.
4. Increment `sync_meta.staging_epoch` and mirror the new value into the staging snapshot and export report (`staging_epoch` field).
5. Rename Maildir files in `cur/` and `new/` to reflect new `:2,FLAGS` suffixes.
6. Write the JSON report to `--report`.

Renaming Maildir files before the database commit is forbidden. The report field `commit_before_rename` must be `true` on success.

## Rollback visibility

If a rename is required, the on-disk filename must still match the pre-sync flags until after the commit completes. Tests may inspect the database mid-sync via `sync_meta.phase`; after a successful sync, `phase` is `committed`.
