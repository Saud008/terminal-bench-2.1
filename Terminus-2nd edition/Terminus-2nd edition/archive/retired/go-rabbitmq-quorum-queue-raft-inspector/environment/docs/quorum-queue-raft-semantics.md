# Quorum queue Raft semantics

Quorum queues replicate a log per queue using a Raft-derived protocol. Unlike generic workflow history compaction, the attested artifact couples queue identity (qq.* names), voter membership epochs, and per-queue message counts recovered only after replaying OCF-style log kinds (config, election, queue, commit).

Leader election records carry node_id and role within a queue replica set, not a global cluster scheduler. Only election kinds move `current_term` / `leader_id`; snapshot baseline seeds `current_term` from `last_included_term`. Snapshot bundles capture `last_included_index` against queue-local state machines; truncation must never resurrect pre-snapshot queue rows when tail replay applies (`index > last_included_index` only).

Membership config changes at or after the membership epoch term must still add voters before export replica lists are frozen. Config term numbers do not themselves become export `term` / `current_term`. This attestation reasons about offline quorum cluster bundles, not Temporal workflow event compaction.
