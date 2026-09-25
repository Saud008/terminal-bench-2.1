# Hold snapshot contract

snapshot-holds writes /app/state/seat-hold-snapshot.json with keys:

- scenario
- engine (venuetixctl)
- hold_snapshot_digest (sha256 hex)
- hold_count
- section_count

hold_snapshot_digest covers unique section_id values sorted ascending, then each hold hold_id:seat_id in database order, then catalog_seed.
