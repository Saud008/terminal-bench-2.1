# Backfill partition

Each as_of_entries row names active_partition for that as_of_ts.

Only offline and online events whose partition equals active_partition participate in joins for that as_of.

Events from other partitions are ignored for that as_of even when TTL-eligible.
