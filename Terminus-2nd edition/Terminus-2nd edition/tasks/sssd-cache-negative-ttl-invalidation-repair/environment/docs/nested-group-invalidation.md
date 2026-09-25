# Nested group invalidation

group_add_member adds member to group. Members may be users or nested groups.

When membership changes, every user with transitive membership in the changed group must be invalidated: remove positive and negative cache rows for that user and increment stats.group_invalidations.

Transitive closure: if eng-all contains developers and developers contains alice, invalidating developers must invalidate alice.

Direct-only invalidation is incorrect when nested_invalidation is true in config.

Explicit invalidate kind removes cache rows for the named user only.
