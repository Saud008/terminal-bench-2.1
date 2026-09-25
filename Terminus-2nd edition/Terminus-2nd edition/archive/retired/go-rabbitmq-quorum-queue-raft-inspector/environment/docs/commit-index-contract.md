# Commit index

`commit_index` tracks the highest index known committed. Queue state entries with `index > commit_index` must not enter staging `queue_states` used for export.

Only `commit` kind markers advance `commit_index` to `max(prior, payload.commit_index)`. Queue (and election/config) entries must not auto-advance `commit_index` to their own index.

Apply commit markers in the control-plane pass before filtering queue rows by the fence so later commits can admit earlier queue indexes in the same segment.
