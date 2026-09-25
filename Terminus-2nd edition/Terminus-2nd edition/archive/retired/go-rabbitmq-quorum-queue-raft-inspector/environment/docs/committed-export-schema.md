# Committed export schema

committed-queue-state.jsonl rows sorted by queue_id ascending only (do not secondary-sort by term):

queue_id, messages, leader_id, term, commit_index, replicas (sorted ascending).

`term` on every export row is the staging `current_term` after replay (election-derived). It is not the term of the last queue or config entry. After a snapshot baseline, `current_term` starts at `last_included_term` and stays there until an `election` kind advances it.

quorum-ledger-seal.json object fields (exact keys):

- `raft_seal` — lowercase hex sha256 of the **seal body** defined below (canonical JSON via `/app/fixtures/digest_util.py` / matching Go map marshal with sorted keys)
- `membership_epoch` — integer equal to staging `current_term`
- `export_row_count` — number of ledger rows written

## raft_seal body (not the full staging witness)

`raft_seal` hashes this object only, with keys sorted, using the same canonical JSON rules as `replay_digest`:

| key | value |
|-----|--------|
| `cluster` | staging cluster id (`--cluster`) |
| `commit_index` | staging commit_index |
| `current_term` | staging current_term |
| `leader_id` | staging leader_id |
| `membership` | staging membership (sorted) |
| `queue_states` | staging queue_states with keys sorted ascending |
| `membership_epoch` | same integer as staging `current_term` |

Do **not** include `replay_digest`, `truncated_before`, `raft_seal`, or `export_row_count` in the seal hash body. Staging witness digest and ledger seal digest are different objects on purpose.
