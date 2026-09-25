# facts.staging.json staging schema

Written by `facts-chain stage` to `/app/state/facts.staging.json`.

```json
{
  "run_id": "batch-20240615",
  "hosts": [
    {
      "inventory_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "hostname": "web-01.example.com",
      "fact_count": 2
    }
  ],
  "total_fact_keys": 2,
  "source_lines": 3
}
```

| Field | Meaning |
|-------|---------|
| `run_id` | Same `--run-id` passed to reconcile/stage |
| `hosts` | One entry per distinct `inventory_uuid` in `fact_snapshots`, sorted by `inventory_uuid` ascending |
| `fact_count` | `SELECT COUNT(*) FROM fact_snapshots WHERE inventory_uuid = ?` |
| `total_fact_keys` | Sum of all `fact_count` values — must equal `SELECT COUNT(*) FROM fact_snapshots` |
| `source_lines` | `SELECT source_lines FROM run_meta WHERE run_id = ?` after reconcile |

`facts-chain stage` must **validate** this schema against `facts.db` **before** writing `/app/state/facts.staging.json`. If validation fails, the staging file must not remain on disk.

Keys are sorted. Trailing newline required.
