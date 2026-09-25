# Authority ticket schema

Path: /app/var/rail/authority.ticket

Fields:
- seed
- scenario
- possession_id: poss- prefix plus first 12 hex chars of SHA-256 over seed:scenario:load_seq
- load_seq: copied from trackgraph.snapshot at compile-trackgraph time
- active: true for the latest row

A new run-possession for the same seed replaces the prior row even when scenario changes.
