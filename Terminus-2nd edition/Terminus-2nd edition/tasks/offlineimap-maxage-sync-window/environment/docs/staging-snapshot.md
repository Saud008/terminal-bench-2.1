# Staging folder snapshot

Path: /app/state/folder-snapshot.json

Schema version 1 fields:

- schema: integer 1
- account: string from imap-meta
- folders: array listing **every** folder from imap-meta (same order as imap-meta), each object `{name, uidvalidity, selected}`
- folder_digest: lowercase hex sha256 of `json.dumps(sorted names of folders where selected is true, separators=(",", ":"))`

Set `selected=true` for folders that pass folder-filter rules. Set `selected=false` for all other IMAP folders (including excluded folders). Excluded folders must still appear in the array for audit visibility.

Publish the snapshot before maxage filtering and ledger mutation.
