# Weight and priority

From /app/config/vrrp.json:

- base_priority: starting priority (typically 100)
- priority_floor: minimum effective priority (never publish below this)
- master_threshold: effective priority at or above this value means role MASTER

Active track weights are negative integers when a track has failed past its fall threshold. Each track defines weight, fall, and rise counts.

Effective priority:

```
effective_priority = max(priority_floor, base_priority + sum(active_weights))
```

The floor applies to the combined base plus weights, not to base alone before adding weights.

Individual track weights must stay within [-50, 0] per track definition.
