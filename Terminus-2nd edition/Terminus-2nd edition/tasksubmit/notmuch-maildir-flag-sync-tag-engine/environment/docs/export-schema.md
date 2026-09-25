# Export report schema

`mailsync sync` and `mailsync publish` write JSON with:

```json
{
  "sync_version": 1,
  "staging_epoch": 1,
  "maildir_files_seen": 5,
  "messages_indexed": 1,
  "messages_skipped": 1,
  "duplicates_merged": 1,
  "flag_renames": 0,
  "tag_writes": 1,
  "threads_resolved": 1,
  "commit_before_rename": true,
  "messages": [
    {
      "message_id": "<reply-a@example.com>",
      "thread_id": "<root-a@example.com>",
      "maildir_relpath": "new/1715508000.3.mail.example.com,S=190:2,FR",
      "flags": "FR",
      "tags": ["finance", "flagged", "replied", "urgent"],
      "keywords_source": "x-keywords"
    }
  ]
}
```

## Counter fields

`maildir_files_seen` counts every regular file under `cur/` and `new/` (before parse filtering).

`messages_skipped` counts maildir files that could not be indexed (missing/invalid Message-ID or unreadable payload).

`messages_indexed` equals `len(messages)` — the number of **dedupe winners** emitted in the report (one row per surviving Message-ID after winner selection in message-id-dedupe.md). It does **not** count duplicate copies discarded during dedupe.

`duplicates_merged` counts duplicate maildir files discarded by dedupe (one increment per loser, not per Message-ID cluster).

`tag_writes` **must equal `messages_indexed` on every successful `sync` and `publish` report**. It is the count of indexed messages whose merged tag set is included in the attestation (same cardinality as `messages`, not a separate count of SQLite `INSERT`/`UPDATE` statements). During `sync`, tags are persisted to SQLite as part of the commit; during `publish`, no new tag upserts occur, but the report still lists every indexed message with its effective merged tags, so `tag_writes` remains `len(messages)` rather than `0`.

`flag_renames` counts Maildir files whose `:2,FLAGS` suffix changed during **sync** only; `publish` sets this to `0`.

`threads_resolved` counts distinct `thread_id` values among indexed messages.

## Message rows

`messages` length equals `messages_indexed`. Sort `messages` by `message_id` ascending. `tags` are lowercased, deduplicated, sorted lexicographically.

`thread_id` is the literal Message-ID string (including angle brackets) of the thread root — the lexicographically smallest Message-ID in the In-Reply-To / References component per message-id-dedupe.md. Do not add a `t-` prefix or strip brackets.
