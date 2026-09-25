# Submission explanations — ecs-archetype-hot-reload-migrator

**Task folder:** tasks/ecs-archetype-hot-reload-migrator/
**Platform form only** — not in upload zip.

## Difficulty Explanation

The ecs-migrate apply command reconciles an ECS SQLite catalog, binary chunk store, and replay journal against a hot-reload layout manifest. Agents struggle because behavior is split across apply-pipeline.md, entity-id-remap.md, archetype-rebuild.md, and several Rust modules. Archetype rebuild must run before stable_id remap, yet both stages read different sources of truth. Stable_id remap updates SQLite only and must not rewrite chunk bytes. The tombstone skip rule is easy to get almost right while still assigning a reserved id. Journal replay means a partial fix can pass bundled entity moves yet fail idempotent second apply or checksum rows.

## Solution Explanation

The oracle copies golden migrator, archetype, entity_id, checksum, and journal sources into ecs-core, rebuilds ecs-migrate, and runs apply against the bundled fixtures. The key insight is the fixed pipeline order: journal-filtered migration steps, archetype table rebuild from chunk bytes keyed by stable_id, then placeholder remap with tombstone reservation in SQLite only. Checksums and report JSON follow only after those stages complete. The compile-time api_contract test locks the public function surface without parsing source strings in pytest.

## Verification Explanation

Pytest fixtures rebuild ecs-migrate before tests and call reset-state.sh. The suite calls ecs-migrate apply via subprocess and compares migration-report.json to an independent Python reference_apply implementation. Tests assert journal cursor behavior, cross-chunk moves, tombstone remap to stable_id 6, chunk checksums, and committed journal state. Hidden cases copy verifier fixtures into temp workdirs before apply so seed data is not mutated across tests. Public API stability is checked by compiling ecs-core tests api_contract.rs rather than grepping Rust sources.
