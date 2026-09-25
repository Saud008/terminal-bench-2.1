# Checkpoint rules

checkpoint.json fields:

merge_seq: integer count of merge attempts.

last_complete_merge: integer count of merges that finished with merge-audit status complete.

Checkpoint merge_seq increments only when a merge attempt starts. last_complete_merge increments only when merge-audit status is complete.

Partial merge failures must leave last_complete_merge unchanged even if merge_seq increased.

Search and export tooling must treat checkpoint as authoritative only when last_complete_merge equals merge_seq.
