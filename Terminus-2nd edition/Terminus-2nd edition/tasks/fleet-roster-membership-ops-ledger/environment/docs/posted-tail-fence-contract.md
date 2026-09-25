# Journal tail fence contract

`commit_index` defines the journal tail fence. Only **queue** kind entries are subject to the fence: queue rows with `index > commit_index` are uncommitted tail and must never appear in committed export rows (and must not contribute to staging `queue_states` used for export).

Election and config kinds are **not** gated by `commit_index`. Leader handoffs and voter membership updates apply when their election/config rules say so, even when no matching commit advance follows the handoff.

Truncation boundaries from `snapshot.json` `last_included_index` interact with tail fences: after truncate-apply, keep only entries with `index > last_included_index`, then honor `commit_index` monotonicity for queue application across the merged epoch.

Verifier scenarios `uncommitted-tail` and `hidden-uncommitted-leader` exercise queue-tail fence drift (queue rows above commit) and same-term leader overwrite without a further commit—not refusal to apply the election itself.
