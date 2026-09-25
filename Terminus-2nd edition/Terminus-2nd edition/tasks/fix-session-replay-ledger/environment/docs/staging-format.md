# Ingest staging snapshot

Default path: `/app/state/ingest-staging.json`

Written after every successful ingest. JSON object with top-level keys `message_count` then `messages`.

## Serialization

The on-disk file is a **canonical byte sequence**, not merely equivalent JSON:

- UTF-8 encoding
- **Compact** JSON: no indentation, no spaces after `:` or `,`
- Object keys in field order shown below (`message_count`, then per-message keys as listed)
- Exactly one trailing newline (`\n`) after the closing `}`

Example bytes (one line plus newline):

```json
{"message_count":4,"messages":[{"session_file":"session_alpha.fix","cl_ord_id":"A-001","exec_id":"E-001","symbol":"AAPL","sending_time":"20240624-10:00:01","msg_type":"8","exec_type":"2"}]}
```

Each `messages` entry includes only: `session_file`, `cl_ord_id`, `exec_id`, `symbol`, `sending_time`, `msg_type`, `exec_type`.

## Ordering

`messages` must list every persisted execution row sorted by `(sending_time asc, cl_ord_id asc, exec_id asc)` — not discovery/file offset order.

`message_count` equals the length of `messages`.
