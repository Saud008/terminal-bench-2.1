# TLS record reassembly

Intake receives capsule frames that may contain partial TLS records. The reassembly layer concatenates deduplicated frame payloads in ascending `(session_quad, seq)` order, then walks the byte stream to extract complete TLS records when at least 5 bytes of header and the declared body length are available.

Incomplete trailing payload bytes stay pending until a later frame completes the record. Reassembly is session-local and must not mix payload bytes across different session_quad values.

## Staged handshake_bytes (exact contract)

The staged `handshake_bytes` field is **not** the output of TLS record filtering. It is the raw concatenation of deduplicated per-session TLS payloads in ascending `(session_quad, seq)` order, with no record headers removed and no reassembly-layer byte dropping.

Emit and the independent parity reference derive JA4 material from this staged byte sequence by locating the first ClientHello handshake body inside the concatenated TLS record stream. The `tls_reasm` module does not define a different staged byte sequence for `handshake_bytes`; `fragment_gap` accounting is defined below.

## fragment_gap (exact contract)

After dedupe, collect the distinct ascending sequence numbers for the session. Sum transport holes as `sum(b - a - 1)` over consecutive sequence pairs `(a, b)`. When that sum is greater than zero, apply a single covered-boundary credit of one:

```
fragment_gap = max(0, hole_sum - 1)
```

When there are no holes, `fragment_gap` stays `0`. The credit is flat (always minus one when any hole exists); it is not computed per missing sequence or per reassembled TLS record.
