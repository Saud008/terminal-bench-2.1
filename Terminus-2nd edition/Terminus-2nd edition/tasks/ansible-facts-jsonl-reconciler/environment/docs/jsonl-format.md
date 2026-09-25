# Ansible facts JSONL stream format

Each non-empty line is one JSON object:

```json
{
  "inventory_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "hostname": "web-01.example.com",
  "collected_at": "2024-06-15T10:00:00Z",
  "facts": {
    "ansible_os_family": "Debian",
    "ansible_memtotal_mb": 8192
  }
}
```

| Field | Rules |
|-------|-------|
| `inventory_uuid` | Required. Stable host identity for merge and diff — **not** `hostname`. |
| `hostname` | Required. Display name only; two hosts may share a hostname in different inventories. |
| `collected_at` | Required. ISO-8601 UTC timestamp ending in `Z`. Used for latest-wins merge per fact key. |
| `facts` | Required object. Keys are fact names; values are JSON scalars (string, number, boolean, or null). |

Lines are processed in file order, but the reconciled value for each `(inventory_uuid, fact_key)` is the value from the row with the **latest** `collected_at` (ties broken by later file position).

Invalid lines (missing fields, non-object `facts`, bad timestamp) must be rejected **before** any SQLite write for that line.
