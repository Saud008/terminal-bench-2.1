# Staging snapshot

Write /app/state/dedup-snapshot.json after replay completes and before export reads ledger stats.

staging_written is true in the snapshot. export_before_ack must be false when export runs after broker persistence.
