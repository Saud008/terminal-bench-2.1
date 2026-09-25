# Attest export

`POST /v1/attest/export` writes `/app/output/attest-report.json`.

## Merge rules

1. Read `/app/state/witness-snapshot.json` when it matches the export `token` and `session_id`.
2. Use snapshot fields for: `last_seq`, `breaches_opened`, `breaches_closed`, `missing_span_total`, `repair_events`, `active_ban_seals`, `witness_seq`, `witness_head`.
3. **Always** read `skew_rejections`, `duplicate_rejections`, and `ticket_rejections` from the **live** session row — never from the snapshot — so HTTP 409/400 rejection counters appear even when no later successful batch refreshed the snapshot.

## Report shape

```json
{
  "token": "...",
  "session_id": "...",
  "last_seq": 0,
  "breaches_opened": 0,
  "breaches_closed": 0,
  "missing_span_total": 0,
  "repair_events": 0,
  "active_ban_seals": 0,
  "skew_rejections": 0,
  "duplicate_rejections": 0,
  "ticket_rejections": 0,
  "witness_seq": 0,
  "witness_head": "...",
  "audit_digest": "..."
}
```

## Audit digest

`audit_digest` is the lowercase hex SHA-256 of the canonical compact JSON encoding of all report fields **except** `audit_digest`, with object keys sorted lexicographically.
