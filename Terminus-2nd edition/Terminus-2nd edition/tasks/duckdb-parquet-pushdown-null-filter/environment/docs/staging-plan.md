# Staging plan

Every filter command writes /app/state/pushdown-plan.json before filter output.

Fields:

- table: catalog table name
- selected_row_groups: row group ids surviving planner and stats pruning
- page_read_order: canonical page order used for decode (null_bitmap, dictionary, data)
- worker_slices: nested arrays of _row_id values assigned per worker
- plan_written: true after successful write

Filter output includes plan_checksum as the first 16 hex characters (8 bytes) of SHA-256 over compact JSON of the staging plan with plan_written true.
