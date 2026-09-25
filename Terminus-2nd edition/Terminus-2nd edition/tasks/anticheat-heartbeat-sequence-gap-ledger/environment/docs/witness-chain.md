# Witness chain

After each successful attest batch (HTTP 200), write `/app/state/witness-snapshot.json`:

```json
{
  "version": 1,
  "token": "...",
  "session_id": "...",
  "witness_seq": 1,
  "witness_head": "<hex>",
  "breaches_opened": 0,
  "breaches_closed": 0,
  "missing_span_total": 0,
  "repair_events": 0,
  "active_ban_seals": 0,
  "last_seq": 0
}
```

## Head formula

```
witness_head = hex(sha256(prev_head || ":" || token || ":" || session_id || ":" || decimal_last_seq || ":" || decimal_witness_seq))
```

`prev_head` is the empty string on the first snapshot for a process write chain; thereafter it is the previous snapshot's `witness_head`. `witness_seq` increments by one on each successful stage write.
