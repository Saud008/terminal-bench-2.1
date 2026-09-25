# facts-diff.json export schema

Written by `facts-chain export`.

```json
{
  "run_id": "batch-20240615",
  "changed_key_count": 2,
  "changed_keys_digest": "a1b2c3d4e5f6...",
  "diff_rows": [
    {
      "inventory_uuid": "550e8400-e29b-41d4-a716-446655440000",
      "fact_key": "ansible_memtotal_mb",
      "old_value": "4096",
      "new_value": "8192"
    }
  ]
}
```

| Field | Meaning |
|-------|---------|
| `changed_key_count` | Count of **distinct** `(inventory_uuid, fact_key)` pairs recorded in `fact_diffs` for this `run_id` — **not** total rows in `fact_snapshots` |
| `changed_keys_digest` | Lowercase hex SHA-256 of newline-joined `inventory_uuid\tfact_key` lines sorted lexicographically |
| `diff_rows` | Rows from `fact_diffs` for `run_id`, sorted by `inventory_uuid`, then `fact_key` |

`old_value` / `new_value` are stringified JSON scalars. Keys are sorted. Trailing newline required.
