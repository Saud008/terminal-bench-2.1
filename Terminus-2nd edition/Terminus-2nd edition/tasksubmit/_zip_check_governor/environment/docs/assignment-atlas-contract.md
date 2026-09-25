# Assignment atlas contract

write-assignment-atlas writes /app/output/hold-assignment-atlas.json when reconcile_pass > 0.

assignments array sorted by queue_pos ascending, then patron_id ascending.

Each row includes queue_pos, patron_id, request_id, copy_id, branch_id.
