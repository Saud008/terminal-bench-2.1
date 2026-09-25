# CLI contract

`zfshold load --scenario <name> --run-id <id>` requires both flags. It resolves the scenario's `inventory.json` from the configured fixture directory and writes `/app/state/inventory.json` plus `/app/state/run-meta.json`.

`zfshold compile --run-id <id>` requires `--run-id`. It reads `/app/state/inventory.json` and writes `/app/state/reclaim-ledger.json`. Compile fails if inventory has not been loaded yet.

`zfshold publish --run-id <id> --output <path>` requires `--run-id`. `--output` is optional; when omitted the atlas is written to the `default_output` path from `/app/config/zfshold.json` (`/app/output/zfs_reclaim_rollout_atlas.json`).

`ingest` is accepted as an alias for `load`. `export` is accepted as an alias for `publish`.

The fixture directory used by `load` is `/app/config/zfshold.json`'s `fixture_dir` field, overridable with the `TB3_FIXTURE_DIR` environment variable for evaluation against alternate scenario roots (for example `/opt/verifier-fixtures/zfshold/scenarios`). The hold-name salt applied by `load` is the config's `hold_name_salt` field, overridable with the `TB3_HOLD_SALT` environment variable.

Unrecognized subcommands or missing required flags must exit non-zero.
