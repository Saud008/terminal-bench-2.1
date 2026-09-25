# JetStream offline journal format

Each line is one JSON object with monotonically increasing seq.

## Operations

| op | fields |
|----|--------|
| PUB | stream, subject, stream_seq, tick |
| CONSUMER_UPSERT | stream, consumer, filter_subject, max_deliver, require_ack_sync |
| DELIVER | stream, consumer, stream_seq, delivery_num, tick |
| ACK | stream, consumer, stream_seq, ack_sync, tick |
| NAK | stream, consumer, stream_seq, delay_ms, tick, timestamp_ms |
| TERM | stream, consumer, stream_seq, tick |

tick is the monotonic replay clock. timestamp_ms is wall metadata only.

Replay writes /app/state/nats-jetstream-stage.json including subject_catalog from ingest.
