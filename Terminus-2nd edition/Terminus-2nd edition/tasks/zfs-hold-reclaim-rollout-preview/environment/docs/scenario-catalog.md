# Scenario catalog

Public fixtures:

- `/app/fixtures/scenarios/basic-hold/inventory.json` — mixed held and free snapshots with healthy free space
- `/app/fixtures/scenarios/clone-blocks-origin/inventory.json` — filesystem clone pinning a snapshot origin
- `/app/fixtures/scenarios/bookmark-target/inventory.json` — bookmark protecting a snapshot target
- `/app/fixtures/scenarios/nested-depth-order/inventory.json` — multiple eligible snapshots requiring depth then txg order
- `/app/fixtures/scenarios/pool-floor-tight/inventory.json` — free space equal to the configured floor

Verifier overlays may appear under `/opt/verifier-fixtures/zfshold/` and follow the same inventory schema. `load` honors `TB3_FIXTURE_DIR` when set.
