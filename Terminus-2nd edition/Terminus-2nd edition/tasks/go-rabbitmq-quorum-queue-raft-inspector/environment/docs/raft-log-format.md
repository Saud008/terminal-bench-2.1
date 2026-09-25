# Raft log format

Files use extension .qlog as JSONL. Each line:

term (int), index (int), kind (noop|config|queue|election|commit), queue_id (string, optional), payload (object).

Election payload fields: node_id, role (candidate|leader|follower).

Config payload fields: op (add_voter|remove_voter), node_id.

Queue payload fields: messages (int), replicas (array of node_id).

Commit payload fields: commit_index (int).

Logs are authoritative for ordering within a cluster directory named by scenario slug.
