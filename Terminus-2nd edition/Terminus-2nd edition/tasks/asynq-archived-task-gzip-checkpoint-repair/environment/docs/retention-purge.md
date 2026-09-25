# Retention purge

purge removes archived rows from SQLite whose archived_at_ms is strictly older than the UTC cutoff given by --before RFC3339.

Compare archived_at_ms against cutoff converted to UTC epoch milliseconds. Do not apply host local timezone offsets when parsing cutoff or comparing archived timestamps.

Rows exactly equal to cutoff remain (strictly older only).

Purge operates on the archived table only; pending tasks are untouched.
