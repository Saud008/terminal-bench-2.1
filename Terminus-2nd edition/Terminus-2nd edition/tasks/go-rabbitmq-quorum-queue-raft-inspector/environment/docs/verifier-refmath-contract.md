# Verifier reference math

Independent replay (agent-visible contract; matches verifier checks) proceeds as follows.

## Load and order

1. Load every `*.qlog` line under the scenario dir; sort globally by `(term, index)` ascending.
2. If `snapshot.json` exists: set baseline `truncated_before = last_included_index`, `commit_index`, `current_term = last_included_term`, `membership`, `queue_states`, membership epoch term = `last_included_term`. Drop entries with `index <= last_included_index` (keep strictly greater).

## Pass 1 — control plane (election / commit / config only)

Walk remaining entries in order:

- `election` — apply leader-election-contract.md (only kind that mutates `current_term` / `leader_id`).
- `commit` — `commit_index = max(commit_index, payload.commit_index)`. Queue kinds must not auto-advance `commit_index`.
- `config` — if `term >= membership_epoch_term`, set epoch to `term` and apply add_voter / remove_voter; keep membership sorted.

## Pass 2 — committed queues

For each `queue` entry with `index <= commit_index`, set `queue_states[queue_id] = payload.messages`.

## Staging witness

Body for `replay_digest` (sha256 canonical JSON, keys sorted):

`cluster`, `commit_index`, `current_term`, `leader_id`, `membership`, `queue_states` (keys sorted), `truncated_before`.

Then attach `replay_digest` on the staging file. Do not feed `replay_digest` back into its own hash.

## Export and seal

Export rows and `raft_seal` follow `committed-export-schema.md`. Seal body includes `membership_epoch` (= `current_term`) and excludes `replay_digest` / `truncated_before`.
