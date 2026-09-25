# Packet index format

Path: `/app/state/pcap.idx`

UTF-8 JSONL — one accepted packet per line, no trailing newline after the last line unless the file is empty.

Each line is a JSON object with sorted keys:

| field | type | notes |
|-------|------|-------|
| `cap_len` | integer | captured length from EPB |
| `file_offset` | integer | byte offset of EPB block start in source capture |
| `interface_id` | integer | zero-based interface index |
| `packet_len` | integer | original on-wire length from EPB |
| `ts_ns` | integer | nanosecond timestamp |

Lines sorted by `(file_offset, interface_id, ts_ns)`.
