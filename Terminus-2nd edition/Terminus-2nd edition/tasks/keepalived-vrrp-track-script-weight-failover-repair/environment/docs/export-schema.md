# Export schema

Output path defaults to /app/output/vrrp-state.json.

```json
{
  "version": 1,
  "virtual_router_id": <int>,
  "role": "MASTER" | "BACKUP",
  "effective_priority": <int>,
  "advert_seq": <int>,
  "active_weights": [{"track": "<name>", "weight": <int>}, ...],
  "last_event_id": "<string or null>"
}
```

active_weights lists tracks with weight_active true sorted by track name ascending (byte order).

Publish only after notify barrier per /app/docs/notify-barrier.md.

Durable publish uses a same-directory temporary file with a .tmp suffix, fsync on the temp file, rename into place, fsync on the final file, and no leftover .tmp sidecar in the output directory after replay completes.
