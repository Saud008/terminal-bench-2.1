# Lead claim

Only log kind `election` updates `current_term` and `leader_id`. Config, queue, and commit entries must never advance `current_term` even when their `term` field is higher.

Apply each election entry in (term, index) order:

1. If `entry.term > current_term`: set `current_term = entry.term`. If `payload.role == "leader"`, set `leader_id = payload.node_id`.
2. Else if `entry.term == current_term` and `payload.role == "leader"`: set `leader_id = payload.node_id` immediately.

Same-term leader records overwrite `leader_id` freely. There is no prior-leader vacation check, no node_id-diff requirement, and no commit_index fence on election application. A later same-term leader election after the last commit marker still becomes the attested leader.

Follower (`role` other than `leader`) records never demote or clear an established `leader_id`.
