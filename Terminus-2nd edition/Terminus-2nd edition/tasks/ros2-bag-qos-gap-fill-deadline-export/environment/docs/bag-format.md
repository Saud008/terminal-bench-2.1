# Bag layout

Each bundle directory under `/app/fixtures/bags/<id>/` contains:

| File | Purpose |
|------|---------|
| `metadata.json` | Topics, QoS profiles, optional `remap` targets |
| `messages.jsonl` | One JSON object per line |

## metadata.json

```json
{
  "topics": {
    "/robot/cmd": {
      "deadline_ms": 40,
      "deadline_clock": "publish"
    }
  },
  "remap": {
    "/legacy/cmd": "/robot/cmd"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `topics` | object | Map of topic name to QoS profile |
| `topics.*.deadline_ms` | integer | Configured deadline in milliseconds |
| `topics.*.deadline_clock` | string | Clock name (`publish` in fixtures) |
| `remap` | object (optional) | Map of raw bag topic → canonical topic |

## Topic remap and payload decode

Apply remap to derive the canonical topic used for gap fill, deadline evaluation, and SQLite export.

Decode payload bytes from each JSONL line using the raw topic field before remap. Exported message rows store the canonical topic string.

| Raw topic | Payload decode |
|-----------|----------------|
| /legacy/cmd | Drop the first payload byte before hashing or export |
| (other) | Use payload bytes as decoded from hex |

Pipeline contracts: /app/docs/gap-fill-rules.md, /app/docs/qos-deadline.md.

## messages.jsonl

Each line is one JSON object:

| Field | Type | Description |
|-------|------|-------------|
| `topic` | string | Logical topic name before remap |
| `seq` | integer | Sequence number per topic |
| `publish_ns` | integer | Publisher timestamp (nanoseconds) |
| `receive_ns` | integer | Recorder receive timestamp (nanoseconds) |
| `payload` | string | Hex-encoded payload bytes |

## catalog.json

```json
{
  "bags": ["gap-monotonic", "gap-dense"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `bags` | array of strings | Bag directory ids under `/app/fixtures/bags/` |

## seeds.json

```json
{
  "seeds": [3, 7, 11]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `seeds` | array of integers | `--seed` values passed to `bag-audit audit` |
