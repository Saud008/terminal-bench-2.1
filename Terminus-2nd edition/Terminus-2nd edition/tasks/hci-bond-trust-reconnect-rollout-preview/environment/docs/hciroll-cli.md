# CLI contract

`hciroll scan --scenario <name> --run-id <id>` requires both flags. It resolves the scenario's `inventory.json` from the configured fixture directory and writes `/app/state/inventory.json` plus `/app/state/run-meta.json`.

`hciroll compile --run-id <id>` requires `--run-id`. It reads `/app/state/inventory.json` and writes `/app/state/reconnect-ledger.json`. Compile fails if the fleet inventory has not been scanned yet.

`hciroll publish --run-id <id> --output <path>` requires `--run-id`. `--output` is optional; when omitted the atlas is written to the `default_output` path from `/app/config/hciroll.json` (`/app/output/hci_reconnect_rollout_atlas.json`).

`load` is accepted as an alias for `scan`.

The fixture directory used by `scan` is `/app/config/hciroll.json`'s `fixture_dir` field, overridable with the `TB3_SCENARIO_DIR` environment variable for evaluation against alternate scenario roots (for example `/opt/verifier-fixtures/hciroll`).

Unrecognized subcommands or missing required flags must exit non-zero.
