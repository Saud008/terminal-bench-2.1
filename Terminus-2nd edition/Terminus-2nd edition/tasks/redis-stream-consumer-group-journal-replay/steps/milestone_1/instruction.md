Implement the offline Redis Streams journal replay tool redisctl under /app. The baseline ingests JSONL journals and writes /app/state/redis-stream-stage.json. Extend the replay engine so pending_log visibility matches temporal ordering invariants in /app/docs/pel-pending-contract.md and /app/docs/stream-journal-format.md.

Pending advances must not appear in pending_log until the matching XACK line has been replayed. Each pending_log row must carry ack_seq equal to that XACK seq. Rebuild redisctl and verify with the bundled journals under /app/data.

The decoy package internal/decoy is not used by replay or export.
