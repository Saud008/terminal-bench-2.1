# Snapshot publish bridge

`mailsync publish` must combine SQLite rows with the latest staging snapshot at /app/state/mail-sync.snapshot.json.

## Staging epoch

The integer `staging_epoch` in the snapshot and export report must match the `staging_epoch` value in `sync_meta` after the most recent successful `sync`. `ingest` copies the current epoch without incrementing. `sync` increments `staging_epoch` only after the SQLite transaction commits and before maildir renames.

## Keyword overlay

When rebuilding a publish report, overlay `x_keywords` from each snapshot `entries` row onto the corresponding database message before tag merge. If snapshot `x_keywords` is non-empty for a message, re-run tag precedence with those keywords even when stored DB keyword tags were cleared or stale. The resulting `keywords_source` must reflect the overlay outcome per tag-precedence.md.

Publish must not rescan the maildir. Renames and `maildir_files_seen` in the publish report come from snapshot metadata and stored rows.

## Publish counters

`flag_renames` is always `0` on publish (no maildir renames).

`tag_writes` still equals `messages_indexed` (length of the `messages` array), not `0`. Publish re-emits the effective merged tag set for every indexed message from SQLite plus snapshot keyword overlay; the counter tracks attested messages, not new SQLite writes performed during publish.
