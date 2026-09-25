# Fixture catalog

Scenarios in `/app/fixtures/catalog.json` exercise the parser end-to-end.

| Scenario | Mode | Focus |
|----------|------|-------|
| `rename-threshold` | generated | `R`/`C` pairs above and below `rename_score_min`; seed permutes pair set |
| `unmerged-matrix` | generated | Tag `u` with `UU`, `AA`, `DU`, `UD` — must not appear as `ordinary` |
| `submodule-gitlink` | static | Mode `160000` on index and worktree fields |
| `nul-paths` | static | Paths with spaces; requires NUL record boundaries |
| `mixed-worktree` | generated | Ordinary, rename, unmerged, and untracked in one stream |

Seeds in `/app/fixtures/seeds.json` drive the generator's rename/copy pair selection and record order permutation.
