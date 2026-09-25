# ECS migrate and query contract

`archectl migrate` loads each world's initial `entities`, applies `journal` ops in file order, then exports archetype tables and entity rows. Initial entities must not overwrite journal effects. `archectl query` and `archectl query-batch` run component-set queries against the same replayed state.

## World generation during replay

Load initial `entities` before the journal. Each accepted initial insert (entity id not tombstoned and successfully placed) increments storage `generation` by 1. Journal mutations then increment `generation` again per the tombstone and sparse-set contracts. Migrate and query exports must report the final `generation` after both phases — initial load counts toward generation and query-cache keys before journal ops are applied.

Exports must be deterministic for a given world JSON and `--seed`. Module contracts:

| Topic | Document |
|-------|----------|
| Migrate snapshot path and publish stage | `/app/docs/migrate-snapshot-schema.md` |
| Replay ledger and two-command migrate pipeline | `/app/docs/replay-ledger-contract.md` |
| Public module interface compatibility under module substitution | `/app/docs/module-interface-contract.md` |
| Component id assignment from `component_names` + seed | `/app/docs/component-registration.md` |
| Archetype identity hash | `/app/docs/archetype-hash.md` |
| Tombstone and respawn rules | `/app/docs/tombstone-semantics.md` |
| Sparse slot generation on recycle | `/app/docs/sparse-set.md` |
| Query result cache | `/app/docs/query-cache.md` |

Migrate export fields: `seed`, `generation`, `component_map`, `archetypes`, `entities`. Each entity row includes `id`, `archetype_hash`, `slot_generation`, and `components` (map of component id → hex data string).

Query export fields: `seed`, `generation`, `query`, `entities`, `cache_hit`.
