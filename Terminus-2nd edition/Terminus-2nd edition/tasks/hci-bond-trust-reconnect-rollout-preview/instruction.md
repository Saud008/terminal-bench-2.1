Fleet operators watch adapter cutover windows where some devices stay eligible for reconnect and others get blocked with a labeled reason. Build hciroll under /app so fleet operators can preview HCI bond-trust reconnect eligibility for every host adapter ahead of a scheduled cutover window. Scan materializes a salted fleet inventory snapshot for the adapter roster under review. Compile writes pairing-gate, resume-hold, power-sequence, and reconnect-storm outcomes into a reconnect ledger. Publish emits a rollout atlas with a deterministic audit digest that downstream operators diff against the prior atlas ahead of the cutover job. The operational rationale for composing these gates lives in /app/docs/cutover-rollout-ops.md. Eligible devices receive a criticality-then-mac rollout sequence so cutover jobs never see nondeterministic ties across hosts in the same cutover cycle.

Place the CLI at /app/bin/hciroll:
  hciroll scan --scenario <name> --run-id <id>
  hciroll compile --run-id <id>
  hciroll publish --run-id <id> --output <path>

Public fleet scenarios sit under /app/fixtures/scenarios (example /app/fixtures/scenarios/basic-reconnect/inventory.json). Evaluation may point TB3_SCENARIO_DIR at /opt/verifier-fixtures/hciroll. Contracts:

- Flag surface: /app/docs/hciroll-cli.md
- Fleet inventory JSON, host_salt, load_seq: /app/docs/fleet-inventory-schema.md
- Pairing gate: /app/docs/pairing-gate-rules.md
- Resume-hold gate: /app/docs/resume-hold-rules.md
- Power-sequence gate: /app/docs/power-sequence-rules.md
- GATT service catalog dedupe: /app/docs/gatt-catalog-rules.md
- Reconnect-storm budget: /app/docs/storm-budget-rules.md
- Reconnect ranking: /app/docs/reconnect-rank-rules.md
- Ledger shape: /app/docs/reconnect-ledger-shape.md
- Atlas digest: /app/docs/rollout-atlas-digest.md
- Cutover operations: /app/docs/cutover-rollout-ops.md
- Scenario catalog: /app/docs/scenario-catalog.md

On-disk run state:
  /app/state/inventory.json
  /app/state/run-meta.json
  /app/state/reconnect-ledger.json
  /app/output/hci_reconnect_rollout_atlas.json (default publish target)
  /app/output/frozen_atlas.json (example alternate path via publish --output)

Hot-path modules (fixed, tests inspect these module boundaries directly): a fleet-intake scan module, a gates directory holding one script per gate (pairing, resume, power, reconnect-storm, GATT catalog), a criticality-ranking module, and an atlas-publish module all live side by side under /app/lib/ alongside the compile orchestrator; the exact directory names are visible in the shipped environment tree. The salted_id and audit_digest fields are both SHA-256 hex digests; /app/lib/digest/salted_id.py provides the shared hashlib-backed hashing helper referenced by the salting and digest formulas in /app/docs/fleet-inventory-schema.md and /app/docs/rollout-atlas-digest.md.

Pytest helpers live in tests/fleet_cutover_harness.py. Independent gate math lives in tests/bond_eligibility_oracle.py and must stay out of /app production imports. Wipe state via /app/scripts/reset-state.sh between independent cases. A decoy mac-formatter module is unused by scan, compile, and publish.

Leave /app/docs/, /app/config/, and /app/fixtures/ unchanged.
