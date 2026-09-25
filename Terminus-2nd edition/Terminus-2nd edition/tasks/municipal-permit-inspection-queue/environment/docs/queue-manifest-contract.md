# Queue manifest contract

Output path defaults to /app/output/permit-queue-manifest.json unless --output overrides it

Manifest fields: scenario, planning_epoch_day, queue_entries, hold_summary, queue_digest.

queue_digest is sha256 hex of compact JSON encoding of queue_entries array only.

queue_entries rows sort by permit_id ascending in the published file.
