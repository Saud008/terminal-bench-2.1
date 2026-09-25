# Session ledger schema

The intake stage writes one JSON object per line to /app/state/session_ledger.jsonl, with rows sorted by session_id ascending, where session_id is the lowercase hex encoding of the 8-byte session_quad.

Each row contains session_id, role_map, handshake_bytes, frame_count, unique_frames, and anomalies. The anomalies object contains fragment_gap, role_flip, and retransmit counters.

The handshake_bytes field stores the deduplicated per-session TLS payload concatenation defined in record_reassembly.md. It is not a TLS-record-filtered or reassembly-trimmed byte sequence.

Bundled capsule fixtures include the exact session identifiers 0a0000010a000002 and c0a80105c0a80109. Those identifiers must remain unchanged in ledger and in the emitted report.
