# Staging snapshot

`mailsync ingest` writes `/app/state/mail-sync.snapshot.json` (override path via snapshot only for tests).

## Schema

```json
{
  "sync_version": 1,
  "staging_epoch": 0,
  "maildir_root": "/app/fixtures/maildir",
  "db_path": "/app/data/mailsync.db",
  "maildir_files_seen": 5,
  "messages_in": 4,
  "messages_skipped": 1,
  "entries": [
    {
      "message_id": "<reply-a@example.com>",
      "maildir_relpath": "new/1715508000.3.mail.example.com,S=190",
      "flags": "",
      "x_keywords": ["finance", "urgent"],
      "mtime_ns": 1715508000000000000,
      "subject": "Re: Root thread A"
    }
  ]
}
```

## Counter fields

`maildir_files_seen` counts every regular file under `cur/` and `new/`.

`messages_skipped` counts files that failed parse/admission (same basis as the export report).

`messages_in` counts **successfully parsed maildir records before Message-ID dedupe** — every admitted file with a valid Message-ID, **including duplicate copies** that dedupe will discard. It is **not** the same as `len(entries)`.

`entries` holds one row per **dedupe winner** (same cardinality basis as export `messages_indexed`). Sort `entries` by `message_id` ascending.

When deriving publish-side `duplicates_merged` from a snapshot, use `messages_in - len(entries)` (floored at zero).

`x_keywords` must preserve parsed X-Keywords header tokens (lowercased). Do not drop the header during ingest.

`staging_epoch` mirrors `sync_meta.staging_epoch` at write time. Only `sync` increments the epoch after commit; see sync-transaction-order.md and snapshot-publish-bridge.md.
