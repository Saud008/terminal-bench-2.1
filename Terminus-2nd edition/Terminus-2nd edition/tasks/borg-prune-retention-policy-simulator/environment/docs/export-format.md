# prune-report.json export schema

Written by borg-prune-sim export.

```json
{
  "clock_skew_adjustment_count": 0,
  "compaction_bytes_reclaimable": 0,
  "compaction_segments_reclaimable": 0,
  "kept_archives": [],
  "legal_hold_count": 0,
  "pruned_archives": []
}
```

| Field | Meaning |
|-------|---------|
| kept_archives | Sorted names surviving retention and holds |
| pruned_archives | Sorted names selected for dry-run prune |
| legal_hold_count | Count of archives protected by holds (exact or prefix) |
| clock_skew_adjustment_count | Archives whose bucket time was clamped |
| compaction_bytes_reclaimable | Sum of original_size_bytes for **pruned** archives |
| compaction_segments_reclaimable | Sum of segment_count for **pruned** archives |

Keys sorted. Trailing newline required.
