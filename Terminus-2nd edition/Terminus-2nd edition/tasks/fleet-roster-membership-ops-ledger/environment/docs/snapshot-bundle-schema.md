# Snapshot bundle

File snapshot.json beside .qlog files:

last_included_term, last_included_index, commit_index, membership (sorted node ids), queue_states map queue_id to messages count.

merge-snapshot applies **exclusive** truncation: discard entries with `index <= last_included_index` (equivalently keep only `index > last_included_index`). Baseline `current_term` comes from `last_included_term` until a later election advances it.
