# Export guard contract

Export path is staging-only:

1. `build_lap_staging` writes `/app/state/lap-staging/<stem>.json`.
2. `export_from_staging(source: &str, stem: &str)` loads the staging file from disk.
3. Export JSON is generated from staging rows without parsing FIT bytes again.

Export JSON schema:

```json
{
  "schema": "fit-lap-export/1",
  "source": "/app/fixtures/fit/recovery.fit",
  "stem": "recovery",
  "staging_version": 1,
  "lap_count": 2,
  "digest": "hex-string",
  "laps": [
    {
      "lap_index": 0,
      "start_time": 3600,
      "end_time": 3660,
      "duration_s": 60,
      "distance_m": 1000,
      "trigger": "time",
      "developer_note": "warmup"
    }
  ]
}
```

Developer notes in export rows bind to each row's `original_index`, even after start-time sorting for staging.
