# Plan resolution contract

`workshop-plan plan` resolves the staged manifest TSV into a mount plan.

## Dependency graph

Edges point from **dependency to dependent** (`to_mod -> from_mod`). The graph
TSV rows are `{dependency}\t{dependent}\t{optional}` where `optional` is `0` or
`1`. Only *admitted* edges appear in the graph and in `edge_count`.

Admission rules, evaluated in manifest declaration order:

- **Target present, constraint satisfied** — edge admitted.
- **Required target missing** — no edge, and an error is recorded:
  `missing required dependency: {from} -> {to} ({constraint})`
- **Target present, constraint fails** — no edge, and an error is recorded:
  `semver constraint failed: {from} requires {to} {constraint} (have {have_version})`
- **Optional target missing** — no edge and *no error*.

Semver comparison is numeric (`1.10.0` satisfies `>=1.2.0`).

When `include_optional_edges` is `false`, optional edges are omitted entirely
from the graph and from `edge_count`, and missing optional dependencies never
error. Required edges are always counted once admitted.

## Mount order

Mount order is computed with Kahn's algorithm, layer by layer. Within each ready
batch (nodes whose remaining in-degree is zero) nodes are sorted in
ASCII-ascending order before emission. The result is **dependency-first**: a
dependency is always mounted before the mod that depends on it.

## Cycle reporting

When a cycle prevents a full topological sort, report the cycle path by:

1. Starting from the **lexicographically smallest node** that is part of a
   cycle.
2. Repeatedly following the **lexicographically first outgoing neighbour** in
   the dependency->dependent adjacency.
3. Emitting the visited nodes joined by `->`, **including the return to the
   start node**.

### Worked example (authoritative)

Given `depends` declarations `mod_a -> mod_b`, `mod_b -> mod_c`,
`mod_c -> mod_a`, the dependency->dependent adjacency is `mod_a -> mod_c`,
`mod_c -> mod_b`, `mod_b -> mod_a`. Walking from `mod_a` and following the
first outgoing neighbour yields:

```
mod_a->mod_c->mod_b->mod_a
```

> **Legacy note (do NOT follow).** An older draft of this document claimed the
> cycle path for the example above was `mod_a->mod_b->mod_c->mod_a`, walking the
> *declaration* order rather than the dependency->dependent adjacency. That
> reversed-edge walk is **wrong**. The authoritative rule is the dependency-first
> first-outgoing adjacency walk shown above, which produces
> `mod_a->mod_c->mod_b->mod_a`. If the two ever disagree, the first-outgoing
> adjacency walk wins.

## Exit codes

- `0` — plan resolved and exported successfully.
- `1` — required dependency missing or a semver constraint failed
  (`fail_on_missing` true), with errors recorded in the plan.
- `2` — a dependency cycle was detected and `emit_on_cycle` is false; the mount
  order is emptied and the cycle path(s) are recorded.
