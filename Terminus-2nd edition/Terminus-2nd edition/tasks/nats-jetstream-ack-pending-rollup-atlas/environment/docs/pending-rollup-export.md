# Pending rollup export schema

natsctl export reads /app/state/nats-jetstream-stage.json only and writes /app/output/pending-rollup.json.

Each consumers row includes:

- stream and consumer names
- pending_count: size of ack-pending map
- high_water_seq: per-consumer durable ack high water, not stream max_seq
- redelivery_due: pending entries whose redelivery_due_tick is less than or equal to tick_ledger

export_pass is echoed from the --pass flag for persistence checks.

Redelivery due ticks are computed from journal tick plus delay_ms on NAK lines.
