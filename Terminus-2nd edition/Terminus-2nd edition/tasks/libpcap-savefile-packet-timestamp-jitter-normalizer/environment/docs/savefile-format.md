Classic libpcap savefile layout (microsecond resolution).

Global header is 24 bytes: magic_number (u32), version_major (u16), version_minor (u16), thiszone (i32), sigfigs (u32), snaplen (u32), network (u32).

Supported magic values are 0xa1b2c3d4 (little-endian microsecond timestamps) and 0xd4c3b2a1 (big-endian microsecond timestamps). Other magic numbers are rejected.

Each packet record is 16 bytes of header followed by incl_len bytes of payload: ts_sec (u32), ts_usec (u32), incl_len (u32), orig_len (u32), then payload.

Multi-byte integers in packet headers use the endianness implied by the file magic. Both ts_sec and ts_usec share the same endianness.

The parser must reject truncated files where a packet header or payload extends past EOF.
