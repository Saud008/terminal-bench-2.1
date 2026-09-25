# Replay ledger contract

Migrate is a **two-command** pipeline. `archectl replay-world` materializes replay state; `archectl migrate` publishes from staged artifacts only.

## Stage 1 — replay-world

`archectl replay-world --world /app/fixtures/worlds/<name>/world.json --seed <seed>`:

1. Replay initial `entities`, then `journal` ops in file order (`storage/world.rs` with `journal_first=false`).
2. Validate replay output (`migrate/ledger.rs`).
3. Write `/app/state/archectl-migrate-snapshot.json`.
4. Write `/app/state/archectl-replay-ledger.json`.

## Replay ledger schema

| Field | Type | Description |
|-------|------|-------------|
| `ledger_version` | integer | Always `1` |
| `seed` | string | `--seed` value used during replay |
| `journal_op_count` | integer | Count of journal ops in the world fixture |
| `generation_digest` | string | Lowercase hex SHA-256 of the verifier-canonical replay payload |
| `sealed` | boolean | Must be `true` after successful replay-world |

The digest payload is built from the staged snapshot with these top-level keys in this exact order: `seed`, `generation`, `component_map`, `entity_ids`.

- `seed` is the snapshot seed string.
- `generation` is the snapshot generation integer.
- `component_map` is copied from the staged snapshot without re-sorting its object keys.
- `entity_ids` is the list of entity ids after sorting snapshot `entities` by `id` ascending.

Serialize that payload as compact JSON with no extra whitespace, equivalent to `json.dumps(payload, separators=(",", ":"))`, then hash the UTF-8 bytes and store the lowercase hex SHA-256 digest in `generation_digest`.

## Stage 2 — migrate

`archectl migrate` loads the migrate snapshot and replay ledger for the same world and seed. It must **not** re-read the world fixture or re-run replay.

Before publish, verify:

- ledger exists and `sealed` is true
- ledger `seed` matches `--seed`
- ledger `journal_op_count` equals the fixture journal length
- ledger `generation_digest` matches the loaded migrate snapshot

Publish rules remain in `/app/docs/migrate-snapshot-schema.md` and `/app/docs/ecs-contract.md`.

## Orchestration

Stage ordering lives in `/app/crates/archecore/src/migrate/runner/mod.rs`. Fixing replay storage alone is insufficient if migrate still re-runs replay or accepts a ledger whose digest does not match the staged snapshot.
