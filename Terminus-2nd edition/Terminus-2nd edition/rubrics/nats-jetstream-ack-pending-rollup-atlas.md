# Platform rubric — nats-jetstream-ack-pending-rollup-atlas

**Task folder:** tasks/nats-jetstream-ack-pending-rollup-atlas/

Agent gates ack-pending subtraction on AckSync durability when require_ack_sync is set, +3
Agent schedules NAK redelivery using journal tick plus delay_ms not wall timestamp_ms, +3
Agent purges ack-pending on TERM when delivery_num reached max_deliver, +3
Agent matches FilterSubject with per-segment asterisk tokens not cross-segment globs, +3
Agent exports per-consumer high_water_seq in pending rollup not stream max_seq, +3
Agent materializes subject catalog into staging snapshot during replay ingest, +2
Agent reads staging snapshot only in export rollup not raw journal input, +2
Agent rebuilds natsctl after editing replay and export packages, +2
Agent ignores decoy wrap and legacy rollup helpers on export hot path, +1
Agent hardcodes pending-rollup.json without running natsctl export, -3
Agent patches only ack pending while leaving NAK tick ledger on wall clock, -3
Agent fixes filter glob but leaves Term max-deliver purge missing, -2
Agent fixes export high water while AckSync still clears pending early, -2
Agent patches only ingest staging while export still uses stream max seq, -2
