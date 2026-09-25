# Snapshot ancestry closure

For a ref snapshot id R, protected ancestry is the set of snapshot ids reached by walking parent_snapshot_id links from R until parent is zero.

Ancestry list sort ids for publish is ascending snapshot_id.

Branch and tag protection uses full ancestry closure, not the ref snapshot alone.
