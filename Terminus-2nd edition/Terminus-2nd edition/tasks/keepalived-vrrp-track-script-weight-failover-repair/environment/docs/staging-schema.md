# Staging schema

Path: /app/state/staging-snapshot.json

```json
{
  "virtual_router_id": <int>,
  "base_priority": <int>,
  "priority_floor": <int>,
  "master_threshold": <int>,
  "effective_priority": <int>,
  "role": "MASTER" | "BACKUP",
  "advert_seq": <int>,
  "notify_pending": <bool>,
  "notify_complete": <bool>,
  "applied_event_ids": ["<id>", ...],
  "tracks": {
    "<name>": {
      "consecutive_fail": <int>,
      "consecutive_ok": <int>,
      "weight_active": <bool>,
      "weight_value": <int>
    }
  }
}
```

After a track recovers (rise threshold met), refresh effective_priority in staging from current active weights. Do not keep a stale effective_priority from the demotion event. The weight module recomputes effective priority only after fail events or when fall logic activates a track; ok events that clear a weight rely on staging to refresh priority.

Manifest at /app/state/staging-manifest.json binds input SHA256 and snapshot SHA256.
