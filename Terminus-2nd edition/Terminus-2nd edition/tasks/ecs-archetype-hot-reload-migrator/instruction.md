Repair the ecs-core migration modules under `/app/crates/ecs-core/src/` in the `/app` Cargo workspace so `ecs-migrate apply` reconciles the ECS SQLite catalog at `/app/data/ecs_meta.db`, the binary chunk store at `/app/data/chunks/`, and the replay journal at `/app/data/replay.journal.json` with the bundled layout at `/app/fixtures/layouts/hot_reload_alpha.json`, and writes `/app/output/migration-report.json` per the contract docs under `/app/docs/`.

## Acceptance criteria

The solution is complete when:

1. Public ecs-core functions match `/app/docs/module-contracts.md` (`cargo test -p ecs-core api_contract` compiles and passes).
2. `ecs-migrate apply` exits 0 against the bundled fixtures.
3. `/app/output/migration-report.json` conforms to `/app/docs/migration-report-schema.md`.

## Requirements

Contract references: `/app/docs/migration-report-schema.md`, `/app/docs/apply-pipeline.md`, `/app/docs/entity-id-remap.md`, `/app/docs/layout-manifest.md`, `/app/docs/chunk-format.md`, `/app/docs/replay-journal.md`, `/app/docs/archetype-rebuild.md`, `/app/docs/module-contracts.md`.

Apply replays journal-filtered migration steps in ascending `order` field sequence (sort layout `migration_steps` by `order` ascending; apply only steps with `order` greater than the journal replay start cursor). Archetypes are rebuilt from live chunk payloads looked up by SQLite `chunk_id` and `slot`, not by chunk-header `stable_id` or stale SQLite columns. Placeholder `stable_id` zero rows are remapped while tombstoned ids remain reserved. Per-chunk checksum rows are emitted after those stages complete.

Entity `stable_id` remap updates SQLite `entities` rows only. Chunk files and `stable_id` bytes embedded in chunk payloads must remain unchanged. For each migration step, `steps_applied[].chunks_touched` counts distinct source chunks whose payloads were rewritten for that step; destination chunks for move steps are not counted.

The `ecs-migrate` binary on PATH must reflect ecs-core source changes. Do not modify `/app/docs/` or `/app/fixtures/`.
