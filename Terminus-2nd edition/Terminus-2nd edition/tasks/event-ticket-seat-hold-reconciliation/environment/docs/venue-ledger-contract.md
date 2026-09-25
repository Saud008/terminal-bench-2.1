# Publish status contract

publish-status writes /app/output/venue-seat-ledger.sqlite and /app/output/hold-conflict-atlas.json when map_pass_count > 0.

seat-state.sqlite table seat_status columns: seat_id, hold_id, order_id, status.

conflicts array sorted by severity descending, then hold_id ascending.

Each conflict row includes hold_id, seat_id, reason, severity.
