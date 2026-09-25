# Staging pipeline

`replay-log` writes `/app/state/raft-staging.json` with: `cluster`, `commit_index`, `current_term`, `leader_id`, `membership`, `queue_states`, `truncated_before`, `replay_digest`.

`replay_digest` hashes the staging fields listed in `verifier-refmath-contract.md` (includes `truncated_before`, excludes the digest field itself).

`merge-snapshot` updates `truncated_before` and recomputes queue_states from snapshot baseline plus exclusive tail replay (`index > last_included_index`).

`audit-membership` writes the replica membership report (`finding_count` = voter count; see `replica-membership-contract.md`).

`export-committed` emits ledger + seal. `raft_seal` uses the **seal body** in `committed-export-schema.md` (includes `membership_epoch`, excludes `truncated_before` and `replay_digest`)—not a hash of the raw staging JSON.

`TB3_FIXTURE_DIR` may point at `/opt/verifier-fixtures/qqraftctl` for hidden scenarios that obey the same contracts.
