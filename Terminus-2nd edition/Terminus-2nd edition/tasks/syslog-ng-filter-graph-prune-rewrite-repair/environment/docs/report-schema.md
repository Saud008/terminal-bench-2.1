# Delivery report schema

Export JSON fields:

- seed (string)
- config_dir (string)
- messages_path (string)
- total_messages (integer)
- dropped_at_facility_gate (integer)
- total_deliveries (integer)
- deliveries (array of {destination, count} sorted by destination)
- rewrite_applied (integer count of messages that received at least one rewrite)

Snapshot at /app/state/routing-snapshot.json adds:

- seed, config_dir, messages_path
- processed_messages, dropped_at_facility_gate, rewrite_applied
- active_routes (array of route_id strings in pruned order, matching graph.conf line order for retained routes)
- config_hash (hex string)
