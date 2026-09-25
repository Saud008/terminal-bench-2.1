# Filter output schema

JSON written to --output path:

- table: string
- matched_row_ids: sorted ascending integers (_row_id values)
- row_count: length of matched_row_ids
- pruned_row_groups: sorted row group ids skipped by planner or stats pruning
- plan_checksum: first 16 hex characters (8 bytes) of SHA-256 over compact JSON of the staging plan with plan_written true

Matched rows must satisfy all active predicates (--is-null, --ts-gte).
