# Snapshot export integrity

export-snapshot writes /app/output/snapshot-bundle.json and /app/state/export-audit.json.

Bundle and audit repeat merged_state_hash, integrity_chain, and snapshot_count (audit) or snapshots length (bundle).

integrity_chain must be consistent with integrity_seed meta and the merged snapshot state hash.

Snapshot rows must be derived from stored snapshot deltas, not hardcoded fixture values.
