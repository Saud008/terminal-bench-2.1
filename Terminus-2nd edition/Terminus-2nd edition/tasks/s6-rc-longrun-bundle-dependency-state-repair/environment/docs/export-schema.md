export emits the effective service graph JSON for a bundle after acyclic validation.

Fields: bundle string, nodes sorted service names, edges array, edge_count integer equal to len(edges).

Each edge object has from, to, and kind. kind is hard or soft. Both hard_deps and soft_deps from ingest must appear in edges.

edge_count must match the parser-derived edge total, not a hand-authored dot file.

export exits 2 with cycle stderr when the hard graph has a cycle, same as validate.
