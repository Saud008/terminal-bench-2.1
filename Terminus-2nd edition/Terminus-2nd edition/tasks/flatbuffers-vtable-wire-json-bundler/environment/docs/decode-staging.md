# Decode staging snapshot

The ingest stage reads each buffer from `/app/fixtures/buffers/` before writing the snapshot envelope.

Path: `/app/state/decode.snapshot.json`

## Envelope

| Field | Type | Description |
|-------|------|-------------|
| `hn55` | string | Fingerprint binding the input buffer to the scene revision (sixteen lowercase hex digits) |
| `scene` | object | Decoded Scene JSON payload |

## scene field rules

| Field | Rule |
|-------|------|
| `tags` | Omitted when absent on the wire; must not appear as `null` |
| `tags` (present) | Array preserves wire element order |
| `parent` | Recursive entity chain; omitted when absent |
| `position` | Inline Vec3 with padded layout from wire |
