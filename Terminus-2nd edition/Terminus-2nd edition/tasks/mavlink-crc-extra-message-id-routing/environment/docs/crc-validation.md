# CRC validation

MAVLink v2 frames start with `0xFD`. CRC-16/MCRF4XX covers bytes after STX through payload, then the message `crc_extra` byte.

| msg_id | name | crc_extra |
|--------|------|-----------|
| 0 | HEARTBEAT | 50 |
| 1 | SYS_STATUS | 124 |
| 24 | GPS_RAW_INT | 24 |
| 11000 | EVENT_LOG | 195 |

CRC input includes the length byte, incompat/compat flags, seq, sysid, compid, and all three little-endian `msg_id` bytes, followed by the full payload.

Validation must use the declared payload length byte and full payload bytes. Skip frames whose wire CRC mismatches or whose `msg_id` is absent from the catalog above; do not abort the whole decode run.
