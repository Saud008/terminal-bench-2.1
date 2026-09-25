# Bookmark gate contract

If any bookmark object's `target` equals a snapshot's `name`, that snapshot is blocked with reason `blocked_bookmark`.

The bookmark's own `name` is never a reclaim candidate and must not be used as the blocked snapshot identity.
