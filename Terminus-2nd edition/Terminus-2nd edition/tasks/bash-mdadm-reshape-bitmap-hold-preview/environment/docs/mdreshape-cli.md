# CLI contract

`mdreshape scan --scenario <name> --run-id <id>` requires both flags. It resolves the scenario's `inventory.json` from the configured fixture directory and writes `/app/state/inventory.json` plus `/app/state/run-meta.json`.

`mdreshape compile --run-id <id>` requires `--run-id`. It reads `/app/state/inventory.json` and writes `/app/state/reshape-ledger.json`. Compile fails if the inventory has not been scanned yet.

`mdreshape publish --run-id <id> --output <path>` requires `--run-id`. `--output` is optional; when omitted the atlas is written to the `default_output` path from `/app/config/mdreshape.json` (`/app/output/mdreshape_eligibility_atlas.json`).

`load` is accepted as an alias for `scan`.

The fixture directory used by `scan` is `/app/config/mdreshape.json`'s `fixture_dir` field, overridable with the `TB3_SCENARIO_DIR` environment variable for evaluation against alternate scenario roots (for example `/opt/verifier-fixtures/mdreshape`).

Unrecognized subcommands or missing required flags must exit non-zero.
