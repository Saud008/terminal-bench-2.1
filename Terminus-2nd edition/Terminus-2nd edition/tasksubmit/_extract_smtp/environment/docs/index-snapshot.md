# Index snapshot contract

After a successful SQLite commit, `mailindex index` persists the export payload before writing JSON.

## Path

Fixed path: `/app/state/thread-index.snapshot.json` (overwrite on every successful index run).

## CLI flow

1. Parse, deduplicate, assign threads, and commit `message_threads` rows in one transaction.
2. Write the snapshot with counters and `messages_indexed_list`.
3. Publish reads the snapshot only — it must not re-query SQLite or re-run assign.

`mailindex publish --output PATH` performs step 3 only.

## Schema

The snapshot wraps the export report plus metadata:

```json
{
  "version": 1,
  "thread_db": "/app/data/thread.db",
  "index_digest": "<sha256 hex of messages_indexed_list rows only>",
  "index_version": 1,
  "files_read": 6,
  "messages_in": 7,
  "messages_indexed": 6,
  "messages_skipped_malformed": 1,
  "messages_deduped": 1,
  "threads_resolved": 3,
  "messages_indexed_list": [
    {
      "message_id": "<root@example.com>",
      "thread_root_id": "<fork@example.com>",
      "date_unix": 1704268800,
      "subject": "Root mail",
      "is_root": false
    }
  ]
}
```

- `messages_indexed_list` must preserve assign-stage order: sorted by `date_unix` ascending, then `message_id` ascending.
- `index_digest` is a SHA-256 hex digest of the compact JSON array of list rows (`message_id`, `thread_root_id`, `date_unix`, `subject`, `is_root`). It must **not** include counters or `thread_db`. The staging writer computes it when persisting; publish must verify the digest before export.
- Publish copies snapshot fields into the final JSON document without re-sorting the list from SQLite.

Missing snapshot must cause publish to fail with non-zero exit.

Implementation lives in `/app/internal/staging/snapshot.go`, `/app/internal/staging/writer.go`, `/app/internal/export/publish.go`, and `/app/internal/export/wrap.go`.
