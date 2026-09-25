# Migrate snapshot schema

`archectl migrate` writes an intermediate migrate snapshot before JSON export.

## Path

Default: `/app/state/archectl-migrate-snapshot.json`

This staged file is written during `archectl replay-world`, then consumed by `archectl migrate`.

## Schema

Same fields as the migrate export in `/app/docs/ecs-contract.md`, plus:

| Field | Value |
|-------|-------|
| `snapshot_version` | Always `1` |

Entity rows in `entities` are sorted by `id` ascending. Archetype rows follow the migrate export rules.

## Pipeline contract

1. **Replay** (`archectl replay-world` via `migrate/runner.rs` with `storage/*`) loads initial entities, applies the journal, writes `/app/state/archectl-migrate-snapshot.json` via `staging/snapshot.rs`, and writes `/app/state/archectl-replay-ledger.json` per `/app/docs/replay-ledger-contract.md`.
2. **Publish** (`archectl migrate` via `migrate/runner.rs` and `export/publish.rs`) reads the snapshot only and writes the migrate JSON export. It must not re-load the world fixture.

The helper in `export/wrap.rs` is not authoritative for publish output; `publish.rs` owns export semantics.
