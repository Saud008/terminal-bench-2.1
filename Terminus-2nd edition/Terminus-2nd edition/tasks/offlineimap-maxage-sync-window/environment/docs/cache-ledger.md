# Cache ledger

SQLite database path: /app/state/sync-ledger.db

Table folder_cache:

- folder TEXT PRIMARY KEY
- uidvalidity INTEGER NOT NULL
- high_uid INTEGER NOT NULL

On each sync, for every folder in the staging snapshot with selected=true:

- If no row exists, insert (folder, uidvalidity, 0).
- If row exists and uidvalidity differs from imap-meta, delete the row and insert fresh (folder, new_uidvalidity, 0).

After a non-dry-run sync completes, set high_uid to the maximum uid synced for that folder among selected messages.

Dry-run must not insert, update, or delete ledger rows.

UIDVALIDITY bumps without reset leave stale high-water UIDs in the ledger and produce wrong exports on the next sync for the same folder.
