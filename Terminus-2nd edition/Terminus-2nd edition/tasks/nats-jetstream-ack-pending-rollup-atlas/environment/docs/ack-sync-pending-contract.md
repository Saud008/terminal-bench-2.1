# Ack-sync and ack-pending contract

When require_ack_sync is true on a consumer, an ACK line must carry ack_sync true before the message leaves the ack-pending map.

Pending subtraction must not run until ack_sync durability is satisfied.

Durable acks advance per-consumer high_water_seq to the acknowledged stream_seq.

The tick field on ACK and NAK lines advances the consumer tick_ledger when greater than the stored ledger.
