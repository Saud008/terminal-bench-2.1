# Entity key contract

Scenarios declare entity_keys in order. Composite entities join on every key column.

Materialized events carry entity_id for single-key scenarios or entity_id plus session_id or device_id fields for multi-key scenarios matching the declared keys.

Matching requires all key columns equal; partial matches must be ignored.
