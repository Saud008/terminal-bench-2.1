# Export report format

Path: /app/output/berth-report.json

```json
{
  "berths": [
    {
      "berth_id": "B-12",
      "concurrent_overlap_minutes": 0,
      "total_dwell_minutes": 0,
      "assignments": [
        {
          "voyage_id": "V001",
          "mmsi": 366999712,
          "arrival_utc": "2024-06-01T10:00:00Z",
          "departure_utc": "2024-06-01T10:45:00Z"
        }
      ]
    }
  ],
  "replay_stats": {
    "accepted": 0,
    "duplicate_rejected": 0
  },
  "staging_digest": "64-char lowercase hex sha256"
}
```

Berths are sorted by berth_id ascending. Assignments within a berth are sorted by arrival_utc then voyage_id.
