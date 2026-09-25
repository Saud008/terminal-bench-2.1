# Reachability graph

Runtime reachability is computed from staging edges where edge_kind is runtime.

Given a binary root norm_purl, collect all packages reachable by following runtime edges from root to dependents transitively. Use breadth-first expansion. Dev and build edge_kind values are ignored for reachability.

A package is reachable from binary B when its norm_purl appears in the transitive closure of B root norm_purl.

Impact rows are emitted only for reachable packages that appear in the staging vulnerability catalog referenced by at least one VEX statement or bundle vuln list entry.

Reachability is boolean on each impact row.
