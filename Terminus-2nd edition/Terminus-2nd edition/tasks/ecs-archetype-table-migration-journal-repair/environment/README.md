# archectl

ECS-style archetype storage, migration journal replay, and component query CLI.

## Two-stage migrate

```bash
archectl replay-world --world /app/fixtures/worlds/tombstone-respawn/world.json --seed alpha-7
archectl migrate --world /app/fixtures/worlds/tombstone-respawn/world.json --seed alpha-7 \
  --export /app/output/migrate.json
```

Contracts: `/app/docs/ecs-contract.md`, `/app/docs/replay-ledger-contract.md`, `/app/docs/migrate-snapshot-schema.md`, `/app/docs/module-interface-contract.md`.

## Environment

| Item | Location / note |
|------|-----------------|
| Rust / Cargo | `/usr/local/cargo/bin` (on `PATH`) |
| rustup home | `/usr/local/rustup` |
| CLI (prebuilt) | `/usr/local/bin/archectl` — rebuild after fixing `/app/crates/archecore/` |
| Workspace | `/app` (`Cargo.toml`, `Cargo.lock`) |
| Network | **Disabled at runtime** — use `cargo build --offline` only |

## Rebuild

```bash
cd /app
cargo build --offline --release --locked -p archectl
install -m 0755 /app/target/release/archectl /usr/local/bin/archectl
```

Fixture worlds live under `/app/fixtures/worlds/`. Batch specs live under `/app/fixtures/batches/`.
