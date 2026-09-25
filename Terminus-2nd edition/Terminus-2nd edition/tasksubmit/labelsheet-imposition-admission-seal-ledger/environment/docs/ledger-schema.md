# Sealed ledger schema

Written sealed JSON object after successful admission:

| Field | Type | Description |
|-------|------|-------------|
| `sheet_width` | u32 | Final PNG width |
| `sheet_height` | u32 | Final PNG height |
| `gutter_px` | u32 | Applied gutter for this ops pass |
| `seed` | u64 | Seed passed to impose |
| `marks` | array | One object per imposed `(mark_id, frame)` |
| `checksum` | string | Lowercase hex SHA-256 |

Each mark object:

| Field | Type |
|-------|------|
| `mark_id` | string |
| `frame` | u32 |
| `sheet_x` | u32 |
| `sheet_y` | u32 |
| `content_w` | u32 |
| `content_h` | u32 |
| `press_rotate` | bool |
| `u0`, `v0`, `u1`, `v1` | f64 (normalized sample window on the sealed sheet) |

## Checksum

Compute over the ledger object **without** the `checksum` field:

1. Recursively sort object keys lexicographically at every nesting level.
2. Serialize with compact JSON (no extra whitespace, separators `,` and `:`).
3. SHA-256 the UTF-8 bytes; emit lowercase hex in `checksum`.

Key order in the written file may differ; only the canonical hash is authoritative.

## Seed policy fields (catalog)

From the catalog JSON at admission time:

- `gutter_px = base_gutter + (seed % gutter_stride)`
- Scalable entries use `scale = 1 + (seed % scale_mod)` on both axes.
