# Link dependency ordering (publish hot path)

Manifest publish computes each library row's dependency_order through **linkorder.sh** (`lt_linkorder_deps`). The older topo.sh helper is retained for local previews only; **publish does not call it**.

Apply the same rules documented in /app/docs/la-format.md (direct subgraph only, Kahn topological sort, lexicographic tie-break among ready nodes, omit broken direct edges entirely).

## Edge direction reminder

When library X lists -lY, Y must appear before X in dependency_order. Work on the direct dependency subgraph for the library being exported — never pull transitive ids into the array.

## Decoy trap

Fixing topo.sh alone does not change published manifests. Publish always sources linkorder.sh after snapshot validation.
