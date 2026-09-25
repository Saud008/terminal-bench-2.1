# Fixture catalog

| Bundle | Exercises |
|--------|-----------|
| `baseline.json` | Sequential frames, empty loss mask |
| `wrap-u32-edge.json` | `frame_seq` across u32 wrap |
| `dup-resend.json` | Duplicate `frame_seq` resend |
| `out-of-order.json` | Frames arrive 1,3,2,4 |
| `loss-bitmask.json` | Non-trivial LE loss mask patterns |
| `partial-tick-batch.json` | Sparse `tick_offset` sets in one frame |

Each bundle lists ordered `packets[].hex` payloads. See `/app/docs/wire-format.md`.
