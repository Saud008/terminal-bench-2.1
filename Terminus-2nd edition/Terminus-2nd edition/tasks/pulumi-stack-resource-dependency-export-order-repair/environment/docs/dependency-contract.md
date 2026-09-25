# Resource dependency graph contract

`pulumi-dep-export order` builds a directed prerequisite graph over every resource URN in the snapshot, writes the result to `/app/state/dep-ledger.json` (see `ledger-schema.md`), topologically sorts the ledger adjacency, and serializes the ordered export report.

Export serialization must load the ledger; re-deriving adjacency from the raw snapshot in `internal/export/` ignores staging and will not match policy. The CLI calls `export.BuildReport(snap, ledgerPath)` with the stable two-argument signature in `/app/docs/module-api-contract.md`.

## Edge rules

All edges point from **prerequisite → dependent** (prerequisite appears earlier in export order).

1. **Explicit `dependencies`** — for each listed URN `d` on resource `r`, add edge `d → r`. Edges are **directed**; reverse edges are incorrect.
2. **Implicit parent** — when `parent` names another resource URN in the snapshot, add edge `parent → r`. Parent edges are required even when `dependencies` is empty.
3. **Provider reference** — when `provider` names a provider URN present in the snapshot, add edge `provider → r`. Provider nodes are part of the graph and export order.
4. **Delete-before-replace** — when `deleteBeforeReplace` is true and `replaces` names `old`, add edge `old → r` and enforce that `old` appears **immediately before** `r` in the final order (no interleaved URNs between the pair).
5. **Component nesting** — do **not** re-parent component children to the component's parent while building the graph. Children keep their `parent` URN until serialization computes `depth`.

## Topological sort

- Use Kahn's algorithm on the directed adjacency list.
- When multiple URNs are ready, pop the one with the **lowest original snapshot index** (stable tie-break). Sorting ready nodes by URN string alone is incorrect.
- Every resource from the snapshot must appear exactly once in the output order.

Incorrect shortcuts (see export-schema.md and fixture-catalog.md for expected report shape) include alphabetical URN ordering, omitting provider nodes, or bypassing the staged ledger during export.
