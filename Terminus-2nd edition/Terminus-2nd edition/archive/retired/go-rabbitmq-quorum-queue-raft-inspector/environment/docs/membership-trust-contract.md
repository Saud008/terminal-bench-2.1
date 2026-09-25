# Quorum membership ops contract

Task identity c4e91b7d2f — host-local OCF Raft quorum membership ops control plane (admit WAL → voter/commit gates → sealed export). Not a generic service repair exercise.

## Ops objective

Offline ops closure of committed qq-prefixed queue message counts from OCF Raft logs and snapshot bundles under term/index ordered admission, last_included_index truncation, commit_index tail fences, quorum leader handoff order, and voter membership epoch gates from config kinds.

## OCF admission ladder

| Log kind | Ops behavior |
|----------|----------------|
| config | add_voter or remove_voter at membership epoch term (does not advance current_term) |
| election | sole updater of current_term / leader_id; same-term leaders overwrite without commit fence |
| queue | qq queue_id message count at log index when index <= commit_index |
| commit | advance commit_index tail fence (queue kinds must not auto-bump commit_index) |

## Integrity failure modes

Index-only sort ignoring term, inclusive snapshot truncation (`>= last_included_index` kept), advancing `current_term` from non-election kinds, hashing the full staging JSON for `raft_seal`, queue rows applied above commit_index, same-term voter adds dropped, or treating `finding_count` as an error counter instead of voter inventory size.

## Export constraint

Identical .qlog fixtures must yield matching raft-staging replay_digest and committed-queue-state.jsonl rows sorted by queue_id. TB3_FIXTURE_DIR selects verifier-only truncation poison overlays.
