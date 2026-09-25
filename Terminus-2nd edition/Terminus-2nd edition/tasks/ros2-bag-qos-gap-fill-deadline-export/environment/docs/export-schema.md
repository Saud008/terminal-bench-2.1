# SQLite export schema

`bag-audit audit --export <path>` produces a SQLite database with these tables:

## `messages`

| Column | Type |
|--------|------|
| `topic` | TEXT |
| `seq` | INTEGER |
| `publish_ns` | INTEGER |
| `receive_ns` | INTEGER |
| `payload_hash` | TEXT (hex SHA-256) |
| `synthetic` | INTEGER (0 or 1) |

Primary key: `(topic, seq)`.

## `deadline_misses`

| Column | Type |
|--------|------|
| `topic` | TEXT |
| `seq` | INTEGER |
| `delta_ns` | INTEGER |
| `deadline_ms` | INTEGER |

| Column | Description |
|--------|-------------|
| topic | Canonical topic where the miss occurred |
| seq | Sequence of the later message in the consecutive pair |
| delta_ns | publish_ns spacing between the pair (nanoseconds) |
| deadline_ms | Configured topics.*.deadline_ms from bag metadata — not the effective threshold after speed and seed adjustment (see /app/docs/qos-deadline.md) |

Miss detection rules: /app/docs/qos-deadline.md.
