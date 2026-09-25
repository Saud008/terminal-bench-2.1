# Message routing

Supported payloads:

**GPS_RAW_INT (24)** — first 12 bytes: `time_boot_ms u32`, `lat int32`, `lon int32` (little-endian).

**EVENT_LOG (11000)** — 8 bytes: `timestamp_ms u32`, `event_seq u16`, `value int16`.

Routing rules:

- Count valid frames per `(sysid, compid, msg_id)` after session filter and dedup.
- Export GPS fixes with signed lat/lon.
- Export EVENT_LOG rows sorted by `timestamp_ms` ascending, then `event_seq`, then `frame_seq`.

Header fields: byte 5 = `sysid`, byte 6 = `compid`.

Seed permutes frame processing order before validation (does not change export sort keys).
