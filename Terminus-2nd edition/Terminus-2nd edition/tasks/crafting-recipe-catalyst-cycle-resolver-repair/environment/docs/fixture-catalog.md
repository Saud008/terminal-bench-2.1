# Fixture catalog

| File | Purpose |
|------|---------|
| `/app/fixtures/recipes/base.json` | Smelt and fold recipes; acyclic |
| `/app/fixtures/recipes/catalyst-chain.json` | Consumed catalyst elixir chain |
| `/app/fixtures/recipes/cycle-trap.json` | Catalyst-only cycle |
| `/app/fixtures/profiles/default.json` | Standard smelt inventory |
| `/app/fixtures/profiles/tight-stacks.json` | Near-full ingot stack for overflow trap |
| `/app/fixtures/catalog.json` | Bundled scenario index |

Recipe overlays may vary `substitutes` and `slot_limit` per seed; agents must not edit bundled fixtures.
