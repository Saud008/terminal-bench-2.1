# SRCDEM binary layout

All integers are little-endian. Magic is exactly `SRCDEM` (6 bytes).

## Header (36 bytes)

| Offset | Size | Field |
|--------|------|-------|
| 0 | 6 | magic |
| 6 | 1 | version (=1) |
| 7 | 1 | flags (bit0 = `loops_packet_stream`) |
| 8 | 4 | signon_tick_base (`u32`) |
| 12 | 2 | tick_count (`u16`) |
| 14 | 2 | str_count (`u16`) |
| 16 | 4 | packet_stream_len (`u32`) |
| 20 | 4 | str_index_off (`u32`, absolute) |
| 24 | 4 | tick_index_off (`u32`, absolute) |
| 28 | 4 | packet_off (`u32`, absolute) |
| 32 | 4 | reserved |

## String index (at `str_index_off`)

`str_count` entries of `u32` absolute offsets to NUL-terminated UTF-8 strings.

## Packet stream (at `packet_off`, length `packet_stream_len`)

| type | code | body |
|------|------|------|
| USERCMD | `0x01` | `u8 str_idx`, `u16 seq`, `u32 arg` |
| SIGNON_RESET | `0x02` | `u32 new_tick_base` |
| STRING_REF | `0x03` | `u8 str_idx` |

`str_idx` is an **unsigned** byte (0–255). A truncated body at EOF is a **partial packet**.

When `loops_packet_stream` is set, the packet stream is replayed once after the first pass. USERCMD rows already emitted for the same `(global_tick, seq)` must not appear again.

## Tick index (at `tick_index_off`)

`tick_count` descriptors, 16 bytes each:

| Offset | Size | Field |
|--------|------|-------|
| 0 | 4 | rel_tick (`u32`, relative to active signon tick base) |
| 4 | 4 | first_packet_idx (`u32`, zero-based packet index inside packet stream) |
| 8 | 2 | packet_count (`u16`) |
| 10 | 2 | storage_ord (`u16`, file-local only) |
| 12 | 4 | reserved |

`global_tick = active_signon_base + rel_tick`. `active_signon_base` starts at header `signon_tick_base`.

When walking a tick row's packet slice in stream order:

- Each SIGNON_RESET sets `active_signon_base = new_tick_base`, increments the signon-reset counter, and does **not** emit a usercmd.
- Recompute `global_tick = active_signon_base + rel_tick` immediately after every SIGNON_RESET so later packets in the **same** tick row use the updated base (mid-tick resets are valid).
- USERCMD packets use the `global_tick` value in effect when that packet is processed.

On a second pass when `loops_packet_stream` is set, reset `active_signon_base` to header `signon_tick_base` before replaying the tick index.

## Multi-file merge

`demo-index build` walks `--root` recursively for `*.dem`, sorts discovered files by **normalized relative path** (forward slashes, case-sensitive byte order), and concatenates timelines in that order. Each file's `source` field in export is that relative path.
