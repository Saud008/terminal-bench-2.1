# Duplicate msg index policy

When multiple rows share the same remapped topic and msg index (seq field), retain the row with the highest relay_pass. Discard lower relay_pass values before monotonic checks. The surviving rows are then sorted by (header_stamp_ns, topic) before timeline ledger emission per /app/docs/timeline-ledger-schema.md.
