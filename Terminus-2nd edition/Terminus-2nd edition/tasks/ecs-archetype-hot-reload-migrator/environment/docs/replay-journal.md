# Replay journal schema

JSON at --journal (default /app/data/replay.journal.json).

```json
{
  "status": "string",
  "commit_cursor": 0,
  "entries": [
    { "step_order": 0, "chunk_id": 0, "committed": true }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| status | string | pending or committed |
| commit_cursor | integer | Highest durable migration step order |
| entries | array | Per-step commit records |
| entries[].step_order | integer | Layout migration step order |
| entries[].chunk_id | integer | Chunk associated with the entry |
| entries[].committed | boolean | Whether the entry is durable |

## Apply replay cursor

| Output field | Rule |
|--------------|------|
| journal_replayed_from | When status is pending, use commit_cursor. When status is committed, use the maximum step_order among entries. |
| Step filtering | Skip layout migration steps whose order is less than or equal to journal_replayed_from. |
| After successful apply | Set status to committed and commit_cursor to the highest applied step order. |
| Re-apply on committed journal | steps_applied must be empty; entities_moved and ids_remapped must be zero. |
