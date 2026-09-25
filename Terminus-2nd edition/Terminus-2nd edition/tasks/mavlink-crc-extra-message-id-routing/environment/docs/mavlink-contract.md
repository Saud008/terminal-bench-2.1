# MAVLink v2 decode contract

`mavctl decode` reads a binary stream, permutes extracted frames with the seed, validates CRC, applies session and dedup policy, optionally checkpoints, routes payloads, and writes JSON export.

```
mavctl decode --input <path> --seed <seed> --export <json> [--checkpoint <db>] [--resume]
```

Seed permutation sorts frames by `fnv1a64("{seed}:{frame_offset}")` before validation. The byte offset is the frame start position in the input stream (after any leading non-frame bytes).

Leading garbage bytes before the first `0xFD` STX are skipped; resync on each STX byte until a complete frame is available or the stream ends.

See `/app/docs/crc-validation.md`, `/app/docs/message-routing.md`, `/app/docs/checkpoint-replay.md`, and `/app/docs/export-schema.md`.
