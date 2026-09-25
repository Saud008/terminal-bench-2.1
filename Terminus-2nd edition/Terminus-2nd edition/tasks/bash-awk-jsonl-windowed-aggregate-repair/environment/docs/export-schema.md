# Export schema

See `/app/docs/contract.md` for ingest rules and `manifest-schema.md` for ledger binding.

`/app/output/aggregate-report.json`:

```json
{
  "agg_version": 1,
  "window_sec": 300,
  "stats": {
    "lines_read": 0,
    "events_accepted": 0,
    "events_deduped": 0,
    "events_skipped_invalid_value": 0
  },
  "windows": [
    {
      "bucket_start": "2024-01-15T08:00:00Z",
      "series": [
        {
          "tenant": "acme",
          "metric": "latency_ms",
          "sum": 30.0,
          "count": 2,
          "min": 10.0,
          "max": 20.0
        }
      ]
    }
  ],
  "footer": {
    "total_events": 2,
    "total_value_sum": 30.0,
    "run_seq": 1
  }
}
```

- `bucket_start` is RFC3339 UTC for the bucket start second.
- `windows` sorted by `bucket_start` ascending.
- Each window's `series` sorted by `tenant` then `metric` ascending.
- Integer-valued aggregates appear as JSON numbers.
- `run_seq` mirrors `/app/state/run-seq.json` `seq` after a successful export.
