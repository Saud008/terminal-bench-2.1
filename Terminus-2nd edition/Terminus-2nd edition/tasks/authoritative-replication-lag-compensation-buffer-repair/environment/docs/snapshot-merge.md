# Snapshot merge ordering

export-snapshot merges snapshot deltas stored in SQLite after ingest.

When ingest recorded snapshot_gap events, the exported bundle must include every snapshot sequence from the minimum through maximum stored delta, inclusive.

gap_fills in snapshot-bundle.json equals gap_events recorded during ingest.

Each exported snapshot row carries seq and state_hash. state_hash values must reflect merged delta history across the full inclusive sequence range, including gap slots.
