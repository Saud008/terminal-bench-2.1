# Trackgraph zone zone-cache schema

Path: /app/var/rail/trackgraph.snapshot

Fields:
- load_seq: monotonically increasing unsigned integer starting at 1 on first compile for a seed
- seed: opaque seed string from CLI
- scenario: scenario name matching fixtures
- blocks: sorted list of block_id values from the scenario
- zone_map: object mapping each block_id to the sorted protected-zone block list for that anchor

Each compile-trackgraph for the same seed increments load_seq even when the scenario name changes.
