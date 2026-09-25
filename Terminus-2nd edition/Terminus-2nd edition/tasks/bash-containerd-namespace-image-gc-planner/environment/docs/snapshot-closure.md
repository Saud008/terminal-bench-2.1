# Snapshot parent closure

Any protected snapshot requires all ancestor snapshots along parent links to remain protected.

Ancestor keys must be included in protected_snapshots even when the lease or pin targeted only a descendant.
