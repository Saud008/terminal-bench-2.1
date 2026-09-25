Implement zfshold, a snapshot reclaim rollout preview on the working Bash baseline under /app. Fleet storage operators reconcile ZFS hold, clone, and bookmark gates across host pools before scheduled destroy windows. They need an eligibility atlas so operational reclaim contracts can be validated before rollout. Build a three stage workflow where load materializes a salted inventory, compile writes the reclaim ledger, and publish emits the rollout atlas. The engineering problem contract in /app/docs/engineering-problem-contract.md states why holds, clone lineage, bookmarks, and pool free-space floors must be evaluated together.

Install the CLI at /app/bin/zfshold with these subcommands:
  zfshold load --scenario <name> --run-id <id>
  zfshold compile --run-id <id>
  zfshold publish --run-id <id> --output <path>

Bundled scenario inventories live under /app/fixtures/scenarios (for example /app/fixtures/scenarios/basic-hold/inventory.json). Fleet rollout expectations before destroy windows appear in /app/docs/fleet-rollout-contract.md. Inventory fields and load_seq rules are defined in /app/docs/inventory-schema-contract.md. Snapshot hold blocking is defined in /app/docs/hold-gate-contract.md. Clone origin protection is defined in /app/docs/clone-lineage-contract.md. Bookmark target protection is defined in /app/docs/bookmark-gate-contract.md. Pool free-space floor gating is defined in /app/docs/pool-floor-contract.md. Eligible reclaim ordering is defined in /app/docs/reclaim-order-contract.md. Compile ledger shape is defined in /app/docs/ledger-schema-contract.md. Publish atlas fields and audit_digest rules are defined in /app/docs/atlas-schema-contract.md. CLI argument contracts are defined in /app/docs/cli-contract.md. Scenario coverage notes are in /app/docs/scenario-catalog.md.

Load persists state at /app/state/inventory.json together with /app/state/run-meta.json; compile persists /app/state/reclaim-ledger.json; publish reads that ledger and emits /app/output/zfs_reclaim_rollout_atlas.json (or another --output path the caller supplies).

Use tests/zfshold_cli_support.py subprocess helpers for CLI invocation and state reset. Independent reference logic is in tests/zfshold_contract_math.py; it is not imported by production scripts. Run /app/scripts/reset-state.sh before cross-run checks. The guid_story_helper decoy module is not on the load, compile, or publish path.

Do not modify /app/docs/, /app/config/, or /app/fixtures/.
