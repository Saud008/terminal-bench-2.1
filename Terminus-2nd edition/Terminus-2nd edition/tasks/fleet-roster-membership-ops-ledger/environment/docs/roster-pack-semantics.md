# Roster pack semantics

Fleet desk scenario packs carry per-queue identity rows. The sealed artifact couples queue identity (`qq.*` names), voter membership epochs, and per-queue message counts recovered only after applying pack kinds (`config`, `election`, `queue`, `commit`).

Lead-claim records carry `node_id` and `role` within a queue replica set. Only `election` kinds move `current_term` / `leader_id`; snapshot baseline seeds `current_term` from `last_included_term`. Snapshot bundles capture `last_included_index`; truncation must never resurrect pre-snapshot queue rows when tail apply runs (`index > last_included_index` only).

Membership config changes at or after the membership epoch term must still add voters before export replica lists are frozen. Config term numbers do not themselves become export `term` / `current_term`.
