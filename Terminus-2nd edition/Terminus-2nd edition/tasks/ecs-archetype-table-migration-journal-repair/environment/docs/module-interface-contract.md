# Archecore module interface contract

Evaluations may rebuild the /app workspace while substituting individual files under /app/crates/archecore/src/ with baseline or golden module versions, then recompile archectl. Agent changes must keep the crate buildable under those substitutions.

## Compatibility requirements

Preserve all of the following across /app/crates/archecore/src/lib.rs, every nested mod.rs, submodule .rs files, and /app/crates/archectl/src/main.rs:

1. Public module layout. lib.rs must continue to expose the same public mods (export, migrate, model, query, staging, storage) and the same crate-level re-exports (migrate_world, replay_world, QueryBatchSpec, WorldSpec, run_query, run_query_batch).
2. Exported function signatures. Callable entry points used across modules must keep names, argument types, and return types compatible, including migrate_world, replay_world, run_query, run_query_batch, staging load/write, ledger load/write/validate_replay/assert_migrate_ready/generation_digest, publish_migrate, apply_export_layer, registration_order, build_component_map, archetype_hash, hash_hex, and cache_key.
3. Shared type compatibility. Types in model.rs and public structs such as World, SparseSet, Slot, and ReplayLedger must remain usable by other modules without signature breakage when only some .rs files are swapped.
4. Module declaration paths. Nested mod.rs files (migrate, storage, query, staging, export, ledger, runner) must keep submodule declarations and pub use re-exports that main.rs and sibling modules rely on.

## Substitution targets

Files that may be replaced independently during rebuild checks include:

| Logical module | Path under /app/crates/archecore/src/ |
|----------------|----------------------------------------|
| runner | migrate/runner/mod.rs |
| ledger | migrate/ledger/mod.rs |
| world | storage/world.rs |
| component | storage/component.rs |
| sparse | storage/sparse.rs |
| archetype | storage/archetype.rs |
| cache | query/cache.rs |
| planner | query/planner.rs |
| staging | staging/snapshot.rs |
| publish | export/publish.rs |
| wrap | export/wrap.rs |

Do not reshape the public API so that a mixed tree of agent modules and baseline or golden modules fails to compile or link through archectl.
