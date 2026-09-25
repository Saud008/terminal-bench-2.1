# Scenario catalog

Public fixtures:

- `/app/fixtures/scenarios/basic-reshape/inventory.json` — one array eligible for a raid5 to raid6 reshape with a clean bitmap and no spare holds
- `/app/fixtures/scenarios/bitmap-internal/inventory.json` — internal bitmap with no clear planned, blocking the array
- `/app/fixtures/scenarios/spare-hold-block/inventory.json` — an array's only spare is fleet-held, blocking the array
- `/app/fixtures/scenarios/degraded-raid5/inventory.json` — a raid5 array below its degraded-disk floor
- `/app/fixtures/scenarios/illegal-path/inventory.json` — a raid6 to raid5 transition, which is not a legal path
- `/app/fixtures/scenarios/window-tight/inventory.json` — one array over the maintenance window budget and one array exactly at the budget
- `/app/fixtures/scenarios/order-criticality/inventory.json` — several eligible arrays, including a raid5 to raid1 shrink path, requiring criticality then name rank

Verifier overlays may appear under `/opt/verifier-fixtures/mdreshape/` and follow the same inventory schema. `scan` honors `TB3_SCENARIO_DIR` when set.
