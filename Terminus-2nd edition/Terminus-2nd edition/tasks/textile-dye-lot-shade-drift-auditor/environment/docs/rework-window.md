# Rework window handling

rework.tsv columns: batch_id, rework_start_epoch, rework_end_epoch, reason_code, supersedes_reading_before_epoch

Bounds are inclusive on both ends. When measured_at_epoch is inside any rework window for the batch, resolve the recipe target as if measured_at_epoch equals supersedes_reading_before_epoch minus one second for precedence purposes.
