# Export JSON schema

```json
{
  "pipeline_version": 1,
  "seed": "collectd-seed-42",
  "batches": ["001-gauge-basic.txt"],
  "flushes": [
    {
      "flush_index": 0,
      "start_epoch": 1704067200,
      "end_epoch": 1704067230,
      "metrics": [
        {
          "canonical_id": "alpha/load/load",
          "ds": "shortterm",
          "value_kind": "gauge",
          "epoch": 1704067200,
          "value": 0.42
        }
      ]
    }
  ],
  "stats": {
    "lines": 4,
    "accepted": 3,
    "rejected": 1
  }
}
```

All numeric values are JSON numbers. `value_kind` is one of `gauge`, `derive_rate`, `counter_delta`, `absolute`.

Flush window bounds follow `/app/docs/metric-contract.md`: `end_epoch` is always `start_epoch + flush_interval_sec` from config (half-open window upper bound).
