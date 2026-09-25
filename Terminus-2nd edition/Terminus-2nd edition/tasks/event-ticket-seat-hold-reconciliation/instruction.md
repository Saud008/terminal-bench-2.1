Arena box-office operators run venuetixctl from the working Go tree at /app to settle ticket payment holds against venue seat inventory before finance close. This data-processing pipeline transforms scenario SQLite bundles into an analytical seat ledger and conflict atlas for finance audit. Each bundle carries section geometry, accessible seat quotas, competing orders, timed authorization timestamps, and reseller release clocks.

Runtime binary: /app/bin/venuetixctl

Operators load one scenario bundle, materialize a hold snapshot digest, reconcile seat-map adjacency and accessibility rules, and publish ledger outputs under /app/output. load-venue writes /app/state/event-venue.sqlite and /app/state/event-manifest.json. Contracts for load-venue, snapshot-holds, reconcile-map, and publish-status are in /app/docs/cli-surface.md. publish-status requires map_pass_count greater than zero in /app/state/map-pass-count.json.

Behavioral contracts live under /app/docs/. Read /app/docs/cli-surface.md, /app/docs/scenario-sqlite-contract.md, /app/docs/seat-hold-snapshot-contract.md, /app/docs/hold-expiry-contract.md, /app/docs/payment-precedence-contract.md, /app/docs/adjacency-block-contract.md, /app/docs/a11y-inventory-contract.md, /app/docs/repeat-run-contract.md, and /app/docs/venue-ledger-contract.md.

Rebuild Go with /app/scripts/verifier-rebuild.sh after edits. Run /app/scripts/reset-state.sh before cross-run verifier cases.

Pytest under /tests loads test_outputs.py, which delegates to test_ethsr_smoke.py, test_ethsr_payment_expiry.py, test_ethsr_map_constraints.py, and test_ethsr_overlay_traps.py. Tests invoke venuetixctl through ethsr_driver and compare venue-seat-ledger.sqlite rows plus hold-conflict-atlas.json to venue_hold_simulator expectations. Bundled scenarios under /app/fixtures include clean-venue, expiry-block, payment-precedence, adjacency-gap, a11y-reserve, stable-rerun, multi-section, and stable-ledger. TB3_FIXTURE_DIR may point at /opt/verifier-fixtures/venuetixctl. TB3_EVENT_CLOCK overrides the scenario clock on overlay cases.

Hold expiry applies a temporal boundary at expires_at. Payment capture ranks by payment_rank ascending, captured_at ascending, and order_id ascending. Spatial seat-map constraints block orphaning a single open seat between two held seats in a row. Accessibility inventory invariants require at least accessibility_min unassigned accessible seats per section after mapping. Repeat runs must produce deterministic ledger rows when the scenario bundle is unchanged.
