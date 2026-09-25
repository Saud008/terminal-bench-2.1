Build the offline NATS JetStream journal replay and per-consumer ack-pending rollup exporter natsctl under /app. The working baseline ingests JSONL jetstream journals, materializes the subject catalog into /app/state/nats-jetstream-stage.json, and supports natsctl replay and natsctl export subcommands.

Replay must maintain ack-pending maps, monotonic tick-ledger redelivery scheduling, FilterSubject token matching, and Term purge semantics per /app/docs/ack-sync-pending-contract.md and /app/docs/filter-subject-tokens.md. Export reads the stage snapshot only and writes /app/output/pending-rollup.json using the schema in /app/docs/pending-rollup-export.md. Journal wire fields are defined in /app/docs/jetstream-journal-format.md.

The internal/decoy and internal/rollup packages are not on the replay or export hot path. Rebuild natsctl and verify with bundled journals under /app/data.
