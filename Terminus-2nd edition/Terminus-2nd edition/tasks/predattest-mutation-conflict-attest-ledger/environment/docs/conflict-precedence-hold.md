# Conflict precedence hold

Within a single record, two or more **scalar** edits (not `multi`) can target
the same `(node uid, attr)`. Exactly one wins.

## Winner rule

Among the conflicting scalar edits for a `(uid, attr)` group:

- the edit with the highest `edit_rank` wins;
- if two share the highest `edit_rank`, the one appearing **later** in the
  record's edit order wins.

`wall_time_ms` is never consulted for precedence. Any implementation that
breaks ties by a wall clock is wrong.

## Outcome reasons

- A `(uid, attr)` group of size one → the single edit is admitted with reason
  `commit_admit`.
- A group of size ≥ 2 → the winner has reason `precedence_winner`; every
  other edit has reason `precedence_loser` and is not applied.
- A `multi` (list) edit is never in a scalar conflict group; it carries
  reason `list_coalesce` (see list-coalesce-rules).

Only winners are applied to the graph. A scalar winner writes its `value`
and, if it carries a non-empty `facets`, sets those facets on the attr.
