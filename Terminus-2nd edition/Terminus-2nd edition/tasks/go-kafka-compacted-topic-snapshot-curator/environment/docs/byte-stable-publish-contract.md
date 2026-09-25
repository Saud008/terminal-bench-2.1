# Idempotent export

Snapshot lines are sorted by canonical_key ascending.

Lineage lines are sorted by partition then offset ascending.

Each JSONL file ends with a trailing newline when non-empty.

A second emit-snapshot without state mutation must produce byte-identical snapshot and lineage files.
