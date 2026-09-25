The mavctl CLI under /app/crates/mavctl decodes MAVLink v2 streams from /app/fixtures/streams/ and emits JSON export per /app/docs/mavlink-contract.md, /app/docs/crc-validation.md, /app/docs/message-routing.md, /app/docs/checkpoint-replay.md, /app/docs/decode-snapshot.md, and /app/docs/export-schema.md. The pipeline applies CRC checksum validation, deterministic seed ordering, session sequence invariants, and idempotent checkpoint resume before snapshot-bound export.

Implement /app/crates/mav-core so mavctl decode and mavctl publish match those documents. Decode must persist /app/state/decode.snapshot.json before export. Publish must read the snapshot only and must not re-parse input bytes.

## Pipeline

Successful mavctl decode runs:

1. Ingest stream bytes, extract, and permute frames from input bytes.
2. Validate CRC and catalog msg_id entries.
3. Session sequence guard and dedup (with optional checkpoint resume).
4. Write /app/state/decode.snapshot.json with merged accepted frames and run counters.
5. Publish export JSON from the decode snapshot only.

Use mavctl decode with --input, --seed, optional --checkpoint and --resume, and --export pointing at a JSON file under /app/output. Use mavctl publish with --export after a successful decode when export must reflect snapshot bytes only.

After decode on merged-regression with seed alpha01, /app/output/merged-regression-alpha01.json and /app/state/decode.snapshot.json must exist.

Do not hardcode bundle outputs. Do not edit /app/docs/, files under /app/fixtures/, or files under /tests.
