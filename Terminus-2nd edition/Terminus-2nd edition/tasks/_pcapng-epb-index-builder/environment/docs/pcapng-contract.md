# PCAPng ingest contract

## Block layout

PCAPng blocks are little-endian. Each block begins with:

| field | size | notes |
|-------|------|-------|
| `block_type` | 4 | e.g. `0x0A0D0D0A` (SHB), `0x00000001` (IDB), `0x00000006` (EPB) |
| `block_total_length` | 4 | **Total** block size in bytes, including both length fields and trailing padding |

The block ends with a duplicate `block_total_length` at offset `block_total_length - 4`.

Advance to the next block using the leading `block_total_length` value — do not recompute length from body size and padding alone.

## Interface Description Blocks

Each IDB encountered in file order defines interface id **0, 1, 2, …** (zero-based). The EPB `interface_id` field is this zero-based index.

Optional `if_name` (option code `2`) is stored for export.

## Enhanced Packet Block body

After the 8-byte block header:

| field | size |
|-------|------|
| `interface_id` | 4 |
| `timestamp_high` | 4 |
| `timestamp_low` | 4 |
| `captured_len` | 4 |
| `packet_len` | 4 |
| `packet_data` | `captured_len` bytes, padded to 4-byte boundary |
| options | TLV options, each padded to 4 bytes |
| trailing `block_total_length` | 4 |

Timestamp in nanoseconds: `(timestamp_high as u64) << 32 | timestamp_low as u64`.

## EPB body CRC option

Option code `0x0EBC` (`epb_body_crc32`) holds a 4-byte little-endian CRC-32 (Ethernet polynomial, same as IEEE 802.3 FCS bit order) over the EPB core bytes starting at `interface_id` through the end of padded `packet_data` (options excluded).

When present, ingest must **reject** the EPB (increment `crc_rejected`, do not index) if the CRC does not match. Do not write rejected packets to `/app/state/pcap.idx`.

## Idempotent replay

Replay key is `interface_id:ts_ns:file_offset` (decimal, colon-separated). Re-ingesting the same key increments `duplicate_rejected` and must not append a second index row.

## Index output

After each successful ingest, rewrite `/app/state/pcap.idx` as documented in `/app/docs/index-format.md` from all accepted rows in the database for that ingest session path (full snapshot, sorted by `(file_offset, interface_id, ts_ns)`).
