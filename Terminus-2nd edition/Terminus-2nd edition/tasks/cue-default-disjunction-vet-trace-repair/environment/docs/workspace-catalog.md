# Workspace catalog

Workspaces under `/app/workspaces/` (see `/app/fixtures/catalog.json`):

| Workspace | Scenario | Key export paths |
|-----------|----------|------------------|
| `ws-lattice` | Bare `disjunct` default with two options (`small`, `large`) | `config.app.size` resolves to `small` or `large` per seed |
| `ws-guard` | Closed schema rejects unknown config fields | — |
| `ws-lineage` | Two-hop embed lineage traces | `config.app.flag` with lineage vet rows |
| `ws-cycle` | Circular embed chain fails evaluation | — |
| `ws-provenance` | Export provenance rows for optional rules | `config.app.tag` optional export path |
| `ws-merged` | Combined disjunct, lineage, closed, and provenance | `config.app.tier`, `config.app.flag`, `config.app.tag` |
| `ws-deep` | Three-hop transitive embed (`App` → `Base` → `Core`); grandparent `rev` field | `config.app.flag` value `on`, `config.app.mode` value `live` |
| `ws-trifold` | Triple-option disjunct (`alpha`, `beta`, `gamma`) with seed-based default | `config.run.choice` resolves to `alpha`, `beta`, or `gamma` per seed |

Seeds: `/app/fixtures/seeds.json` (`alpha01`, `beta17`, `gamma99`, `delta42`, `epoch07`).
