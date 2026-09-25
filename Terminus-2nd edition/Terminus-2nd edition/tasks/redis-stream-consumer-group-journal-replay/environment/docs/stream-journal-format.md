# Stream journal format

Offline replay consumes newline-delimited JSON at paths under /app/data. Each line is one event with monotonic seq.

Required fields: seq, op, timestamp_ms. Supported op values: XADD, XREADGROUP, XACK, XGROUP, XAUTOCLAIM.

XADD uses stream, id, fields. XREADGROUP uses stream, group, consumer, ids. XACK uses stream, group, ids. XGROUP CREATE uses sub CREATE, stream, group, id, mkstream. XAUTOCLAIM uses stream, group, consumer, min_idle_ms, timestamp_ms.

Replay writes /app/state/redis-stream-stage.json. The pending_log array records PEL visibility only after the matching XACK line has been applied during replay. Each pending_log entry carries ack_seq equal to the XACK journal seq.
