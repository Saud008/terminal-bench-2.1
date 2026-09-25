# Games playtest workflow

Each playfield board playtest must:

1. Load one square-grid playfield board JSON pack and apply optional `--seed` playtest perturbations.
2. Audit portal rows and off-mesh jump links under bidirectional, linear-snap, and region-match rules.
3. Count 4-connected walkable zones and write the playfield staging snapshot under `/app/state/playfield-staging/`.
4. Emit either a validate export or a path export (`--from` / `--to`) matching `spec.md` and the playtest win conditions.

Subcommands: `validate` and `path`. Flags and board overlay roots are cataloged in `playfield-board-catalog.md`. Independent verifier reference math recomputes the same exports without treating scout_decoy as part of the playtest path.
