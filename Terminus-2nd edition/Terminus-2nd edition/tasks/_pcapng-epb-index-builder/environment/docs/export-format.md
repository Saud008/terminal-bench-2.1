# Capture summary export format

```
pcap-index export --db /app/state/index.db --out /app/output/capture-summary.json
```

## Top-level schema

```json
{
  "packet_count": 0,
  "interfaces": [ ... ],
  "index_digest": "lowercase sha256 hex of /app/state/pcap.idx bytes",
  "crc_rejected": 0,
  "duplicate_rejected": 0
}
```

## `packet_count`

Count of **distinct** `ts_ns` values across all accepted index rows (one packet per unique timestamp globally, even when multiple interfaces share a timestamp).

## `interfaces[]`

Each element:

| field | type | notes |
|-------|------|-------|
| `interface_id` | integer | zero-based |
| `if_name` | string | from IDB `if_name` option, or `iface{N}` if absent |
| `packet_count` | integer | accepted rows on this interface |

Sorted by `interface_id`.

## Counters

`crc_rejected` and `duplicate_rejected` are cumulative SQLite counters after the latest ingest on this database.

## `index_digest`

Lowercase hex SHA-256 of the exact on-disk bytes of `/app/state/pcap.idx` at export time.
