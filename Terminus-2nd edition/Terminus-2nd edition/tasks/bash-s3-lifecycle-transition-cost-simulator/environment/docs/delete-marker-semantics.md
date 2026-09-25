# Delete marker semantics

The current version for a key is the version with the greatest last_modified timestamp. Ties break by last inventory line order.

When the current version is a delete marker, lifecycle transitions and expiration target **noncurrent** versions only. The delete marker itself is never transitioned.

delete_marker_orphan_count in simulation counts noncurrent versions whose current version is a delete marker and that remain billable after simulation.
