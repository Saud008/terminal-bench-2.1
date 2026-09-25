# Broker ack barrier

Export high_water for each stream must not exceed broker_acked_max persisted for that stream.

Persist broker ack state to /app/state/broker-ledger.json before building export output. export_barrier_ok is true only when every stream satisfies high_water <= broker_acked_max.
