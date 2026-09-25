The archectl CLI at /app replays ECS-style migration journals and runs component queries against fixture worlds under /app/fixtures/worlds/. Bundled migrate and query exports do not match the behavioral contracts.

Update the Rust library in /app/crates/archecore/src/ so archectl replay-world, archectl migrate, archectl query, and archectl query-batch produce exports consistent with /app/docs/ecs-contract.md and the linked contracts under /app/docs/.

Migrate is a two-stage pipeline. Stage 1: archectl replay-world loads the world fixture, applies the journal, and writes two state artifacts: /app/state/archectl-migrate-snapshot.json and /app/state/archectl-replay-ledger.json. Stage 2: archectl migrate publishes the migrate JSON export from those staged artifacts only. It must not re-read the world fixture or re-run replay.

Stage 1 outputs:
- /app/state/archectl-migrate-snapshot.json
- /app/state/archectl-replay-ledger.json

The replay ledger generation digest must match the replay-ledger contract exactly: hash a compact JSON payload whose top-level keys appear in this order, seed, generation, component_map, entity_ids; keep component_map in the same order stored in the staged snapshot; derive entity_ids from snapshot entities sorted by id ascending; and serialize without added spaces or pretty printing before computing the lowercase hex SHA-256 digest. Sealed ledger rules, generation digests, and snapshot schema are in /app/docs/replay-ledger-contract.md and /app/docs/migrate-snapshot-schema.md. Query exports, component registration, archetype hashing, tombstones, sparse sets, and query-cache semantics remain in /app/docs/ecs-contract.md and its linked module contracts.

Bundled worlds use PRIMARY_SEED alpha-7 from /app/fixtures/seeds.json unless a test passes a different value to --seed. Evaluations may set VERIFIER_SEED (default gamma-9001) for procedural fixture checks.

Evaluations may rebuild the project while replacing individual Archecore modules under /app/crates/archecore/src/ with baseline or golden versions. Changes must preserve public module interfaces, exported function signatures, and shared type compatibility across lib.rs, nested mod.rs files, submodule sources, and /app/crates/archectl/src/main.rs. Full rules are in /app/docs/module-interface-contract.md.

The environment has no outbound network access. Rust and Cargo are on PATH at /usr/local/cargo/bin. Rebuild and reinstall archectl after source changes (cargo build --offline --release --locked -p archectl). Example commands are in /app/README.md. Do not edit /app/fixtures/ or /tests/.
