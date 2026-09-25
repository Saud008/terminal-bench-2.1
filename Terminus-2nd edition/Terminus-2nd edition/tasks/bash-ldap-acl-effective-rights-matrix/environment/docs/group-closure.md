# Group closure

Group membership is transitive. When a group contains another group as a member, nested members expand before ACL subject matching. Direct-only membership is insufficient for readers nested under admins.

## Staging snapshot fields

Ingest writes two related structures on the staging snapshot:

- **`group_graph`** — direct edges from the groups TSV: each group DN maps to the sorted list of member DNs listed on that group's row. No transitive expansion.
- **`group_closure`** — transitive expansion of `group_graph`. Each group DN maps to the sorted list of **terminal member DNs** reachable through nested groups.

Both keys are required. Export reads them from the staging snapshot; do not re-parse the groups TSV during export.

## Transitive expansion rules

Cycle-safe depth-first expansion:

- Start from each group key in `group_graph`.
- For each direct member:
  - if the member DN is itself a group key in `group_graph`, recurse into that group and union its terminal members;
  - otherwise add the member DN as a terminal member.
- **Do not** add intermediate group DNs to `group_closure` values — only leaf (non-group) members belong in the closure list.

Example: if `cn=admins` contains `cn=readers` and `cn=readers` contains `cn=alice`, then `group_closure["cn=admins,..."]` includes `cn=alice,...` but not `cn=readers,...`.

## ACL subject matching

A group ACE matches a probe subject when the normalized probe subject DN equals the ACE subject DN, or when the probe subject appears in `group_closure[ace_subject_dn]`. When the ACE group is absent from `group_closure`, fall back to direct membership in `group_graph[ace_subject_dn]`.

`staging_fingerprint` member lines are built from `group_closure` pairs (`member;{group};{member}`), not from `group_graph` direct edges alone.
