# Ownership ordering

o ownership lines must be applied before any remove pass deletes the target path. When both o and r! target the same path and the remove gate would pass, the export action trace must list ownership before remove, and the final tree must not contain the path.

If ownership cannot run because the path is already absent, emit no ownership action for that line.

Ownership updates mode, user, and group fields on the existing tree entry without changing timestamps.
