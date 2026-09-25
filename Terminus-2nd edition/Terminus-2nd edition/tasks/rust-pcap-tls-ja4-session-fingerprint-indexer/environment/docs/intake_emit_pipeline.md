# Intake and emit pipeline

## Intake

```
ja4idx intake --capsules-dir <DIR> --ledger /app/state/session_ledger.jsonl
```

Intake reads all `.cap` files, deduplicates retransmits, assigns roles, counts anomalies, and writes **one JSON object per line** to the ledger file.

Ledger lines must be sorted by `session_id` ascending (hex encoded session quad).

Each ledger row contains:

- `session_id`, `role_map`, `handshake_bytes` (raw deduplicated payload concatenation per record_reassembly.md)
- `frame_count`, `unique_frames`, `anomalies` object with `fragment_gap`, `role_flip`, `retransmit`

Role assignment uses the **first observed direction byte** per endpoint: the endpoint that sends the first client-direction frame is the client; the peer is the server.

Retransmit dedupe drops later frames with the same `(session, seq)` **or** identical TLS payload hash as an earlier frame.

`fragment_gap` follows the exact hole-sum credit in record_reassembly.md: sum `(b - a - 1)` over consecutive distinct sequences, then `max(0, hole_sum - 1)` whenever any hole exists.

## Emit

```
ja4idx emit --ledger /app/state/session_ledger.jsonl --out /app/output/session_index.json
```

Emit computes JA4 strings, copies anomaly counters, sorts sessions by `session_id`, and sets `totals.session_count` to the number of sessions.

## Alternate capsule directory

When TB3_CAPSULE_DIR points at an alternate `.cap` directory (see hidden_capsule_override.md), intake must read capsules from that path instead of the bundled fixtures directory.
