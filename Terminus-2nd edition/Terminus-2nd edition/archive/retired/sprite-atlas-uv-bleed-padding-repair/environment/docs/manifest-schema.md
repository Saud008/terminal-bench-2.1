# Manifest schema

Written JSON object:

| Field | Type | Description |
|-------|------|-------------|
| `atlas_width` | u32 | Final PNG width |
| `atlas_height` | u32 | Final PNG height |
| `padding_px` | u32 | Applied padding for this pack |
| `seed` | u64 | Seed passed to pack |
| `sprites` | array | One object per packed `(glyph_id, frame)` |
| `checksum` | string | Lowercase hex SHA-256 |

Each sprite object:

| Field | Type |
|-------|------|
| `glyph_id` | string |
| `frame` | u32 |
| `atlas_x` | u32 |
| `atlas_y` | u32 |
| `content_w` | u32 |
| `content_h` | u32 |
| `rotate` | bool |
| `u0`, `v0`, `u1`, `v1` | f64 |

## Checksum

Compute over the manifest object **without** the `checksum` field:

1. Recursively sort object keys lexicographically at every nesting level.
2. Serialize with `serde_json` compact form (no extra whitespace).
3. SHA-256 the UTF-8 bytes; emit lowercase hex in `checksum`.

Key order in the written file may differ; only the canonical hash is authoritative.

## Seed policy fields (catalog)

From the catalog JSON at pack time:

- `padding_px = base_padding + (seed % padding_stride)`
- Scalable entries use `scale = 1 + (seed % scale_mod)` on both axes.
