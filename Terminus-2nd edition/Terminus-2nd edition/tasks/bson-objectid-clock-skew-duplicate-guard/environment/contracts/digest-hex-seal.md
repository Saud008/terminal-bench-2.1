# Digest-hex seal

Each intake batch creates `/app/state/digestseal-batch.json` before oidstore persist.

`batch_digest` is lowercase hex SHA-256 over UTF-8 lines joined by `\n` with **no trailing newline**:

1. `machine_id`
2. `now_unix` as a decimal integer string
3. one line per request-order document: `client_seq|compact-payload`

**compact-payload** means JSON with no insignificant whitespace: separators are `,` and `:` with no spaces after either token. This matches Go `encoding/json.Compact` and Python `json.dumps(payload, separators=(",", ":"))`. Preserve object key order from the intake payload bytes; do **not** sort keys. Pretty-printed or space-padded JSON is wrong for the digest input.

Example line for `client_seq=3` and payload `{"tag":"a","n":1}`:

```text
3|{"tag":"a","n":1}
```

The oidstore must load and verify this digest from the staged snapshot rather than reuse the live request body.
