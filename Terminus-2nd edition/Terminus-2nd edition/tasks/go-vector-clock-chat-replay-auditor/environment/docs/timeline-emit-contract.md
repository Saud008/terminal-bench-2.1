# Timeline emit contract

## Gate

emit-timeline exits non-zero when reconcile_revision in /app/state/reconcile-revision.json is zero.

## Row shape

Each JSONL line:

| Field | Type |
|-------|------|
| seq | int | 1-based sequence in emitted timeline |
| event_id | string |
| type | string |
| sender | string |
| vector_clock | object |
| visible | bool | false when moderation hides a message |
| timeline_digest | string | Present only on final row |

## Visibility

Messages from users with effective ban or kick moderation are not visible.

Messages during active mute intervals are visible false.

## timeline_digest

SHA-256 lowercase hex of canonical JSON:

```json
{
  "room": "ROOM",
  "scenario": "SCENARIO",
  "rows": [ ... all rows except timeline_digest field ... ]
}
```

Compact JSON, sorted keys. The digest is stored only on the last JSONL line.

## Sort order

Rows follow causal sort from vector-clock-contract.md. Suppressed duplicate receipts are omitted entirely.
