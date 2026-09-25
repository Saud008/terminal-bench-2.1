# Platform rubric — event-ticket-seat-hold-reconciliation

**Task folder:** tasks/event-ticket-seat-hold-reconciliation/

Agent imports scenario SQLite bundles into event-venue.sqlite with manifest sidecar via load-venue, +2
Agent writes seat-hold-snapshot.json with staging digest and hold counts after snapshot-holds, +3
Agent skips seat holds whose status is not active or whose expires_at is before the event clock, +3
Agent ranks competing holds by lower payment_rank then captured_at then order_id, +3
Agent blocks assignments that would orphan a single open seat between two held seats in a row, +3
Agent preserves at least accessibility_min unassigned accessible seats per section after mapping, +3
Agent increments map_pass_count only after reconcile-map writes seat-map-pass.json, +2
Agent blocks publish-status until map_pass_count in map-pass-count.json is greater than zero, +2
Agent exports venue-seat-ledger.sqlite rows sorted by seat_id matching assignment contract, +2
Agent publishes hold-conflict-atlas.json with run_stamp and severity-sorted conflicts, +2
Agent honors TB3_EVENT_CLOCK override on hidden overlay trap scenarios, +2
Agent rebuilds venuetixctl via verifier-rebuild.sh before subprocess CLI verification, +2
Agent treats hold expiry as inclusive on expires_at at the scenario event clock, -3
Agent reverses payment_rank precedence so higher rank captures seats first, -3
Agent assigns seats that violate adjacency orphan protection in a row, -3
Agent drops accessible inventory below section accessibility_min after reconciliation, -3
