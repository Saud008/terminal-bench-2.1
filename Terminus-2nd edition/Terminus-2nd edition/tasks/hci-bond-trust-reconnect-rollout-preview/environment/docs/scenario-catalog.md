# Scenario catalog

Public fixtures:

- `/app/fixtures/scenarios/basic-reconnect/inventory.json` — one device eligible for reconnect with matched address types, a cleared resume slot, and a `cycle` power plan
- `/app/fixtures/scenarios/pairing-mismatch/inventory.json` — an address-type drift with pairing not confirmed, blocking the device
- `/app/fixtures/scenarios/resume-armed-block/inventory.json` — a non-empty resume token with `resume_cleared: false`, blocking the device
- `/app/fixtures/scenarios/power-sequence-gap/inventory.json` — an `off_first` adapter with a device missing `disconnect_before_power`
- `/app/fixtures/scenarios/reconnect-storm/inventory.json` — battery probes whose debounced attempt count exceeds the configured budget
- `/app/fixtures/scenarios/gatt-duplicate-uuids/inventory.json` — mixed-case duplicate GATT UUIDs requiring lowercase dedupe
- `/app/fixtures/scenarios/cutover-order/inventory.json` — several eligible devices across two adapters, requiring criticality then mac rank

Evaluation overlays may appear under `/opt/verifier-fixtures/hciroll/` and follow the same fleet inventory schema. `scan` honors `TB3_SCENARIO_DIR` when set. Hidden overlay cases include `/opt/verifier-fixtures/hciroll/hidden-resume-cleared-override/inventory.json` (a stale resume token that must stay eligible once cleared) and `/opt/verifier-fixtures/hciroll/hidden-storm-debounce-window/inventory.json` (battery probes inside one debounce window that must only count once).

Verifier run-ids are caller-chosen labels with no reserved format; cross-adapter ranking cases may use a run-id such as `rank-cross-adapter`.
