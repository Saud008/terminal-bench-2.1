# Capsule capture format

Capsule files use extension `.cap` under the intake directory.

## File header

| Offset | Size | Encoding | Field |
|--------|------|----------|-------|
| 0 | 4 | ASCII | Magic `CAPS` |
| 4 | 4 | uint32 LE | Frame count |

## Per-frame record

| Field | Size | Notes |
|-------|------|-------|
| session_quad | 8 | First four bytes are client IPv4 octets; second four are server IPv4 octets |
| seq | 4 | **Little-endian** transport sequence |
| direction | 1 | `0` = client-to-server, `1` = server-to-client |
| retransmit | 1 | Non-zero when this frame is a retransmit |
| payload_len | 2 | uint16 LE |
| tls_payload | N | Raw TLS record bytes (may be partial) |

Frames must be processed in ascending `(session_quad, seq)` order after directory read.
