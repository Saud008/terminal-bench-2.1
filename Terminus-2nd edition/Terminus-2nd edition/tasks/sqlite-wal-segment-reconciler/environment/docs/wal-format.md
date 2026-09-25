# SQLite WAL sidecar segment layout (`<db>-wal`)

The reconciler reads a **segment sidecar** beside the SQLite database. Layout mirrors SQLite WAL framing, but frame integrity uses the CRC32 rolling scheme below (not SQLite engine checksums).

## WAL header (32 bytes, big-endian integers)

| Offset | Size | Field |
|--------|------|-------|
| 0 | 4 | Magic `0x377f0682` |
| 4 | 4 | File format version (3007000) |
| 8 | 4 | **Page size** in bytes |
| 12 | 4 | Checkpoint sequence |
| 16 | 4 | Salt-1 |
| 20 | 4 | Salt-2 |
| 24 | 4 | Header checksum-1 (unused; may be zero) |
| 28 | 4 | Header checksum-2 (unused; may be zero) |

## Frame layout

Each frame occupies `24 + page_size` bytes after the header.

| Offset (within frame) | Size | Field |
|-----------------------|------|-------|
| 0 | 4 | Page number |
| 4 | 4 | Database size in pages |
| 8 | 4 | Salt-1 copy |
| 12 | 4 | Salt-2 copy |
| 16 | 4 | Checksum-1 |
| 20 | 4 | Checksum-2 |
| 24 | page_size | Page payload |

Frame count: `(wal_file_size - 32) / (24 + page_size)`.

## CRC32 rolling checksum

Seed frame 1 with WAL header `salt1` / `salt2`. For each frame, with header16 = bytes 0–15 and payload = bytes 24..:

```
c0 = crc32(header16[0:8],  salt1)
c1 = crc32(header16[8:16], salt2 ^ c0)
c0 = crc32(payload,        c1)
c1 = crc32(header16,       c0)
```

Stored checksum-1/checksum-2 must equal final `c0` / `c1`. **Verify checksum before recording the frame as applied.**

## Sidecar snapshot

When `<db>.wal.snap` exists and `<db>-wal` is missing, restore the sidecar from the snapshot before parsing.
