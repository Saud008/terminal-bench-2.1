# Revenue capacity snapshot seal

freeze-capacity-snapshot emits /app/state/capacity-snapshot.json with capacity_fingerprint, room_count, and maintenance_count.

capacity_fingerprint is sha256 hex over sorted room_id:room_type_id pairs joined by pipe, then pipe catalog_seed, then pipe sorted maintenance rows formatted as room_id:start:end.

Maintenance window rows belong in the digest payload.
