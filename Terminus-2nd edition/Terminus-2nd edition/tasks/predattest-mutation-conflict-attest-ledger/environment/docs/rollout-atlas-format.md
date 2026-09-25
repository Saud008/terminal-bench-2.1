# Rollout atlas format

`publish` writes the compiled rollout ledger (the "atlas") as pretty JSON with
sorted keys. It is identical to the ledger `compile` stores under run state.

## Top-level fields

```json
{
  "schema": "wavehold.rollout.v1",
  "schema_marks": ["labels"],
  "applied_edits": 6,
  "held_records": 1,
  "held_attrs": ["drain_token"],
  "last_commit_index": 7,
  "outcomes": [ ... ],
  "nodes": [ ... ],
  "atlas_digest": "<64 hex chars>"
}
```

- `schema` — always `wavehold.rollout.v1`.
- `schema_marks` — final schema epoch, sorted ascending (committed records only).
- `applied_edits` — count of edits actually written (scalar winners + list
  appends that added an entry), across committed records only.
- `held_records` — number of records held at preflight.
- `held_attrs` — sorted, de-duplicated attrs held by the deny-pin gate.
- `last_commit_index` — `commit_index` of the last record in the wave (0 if empty).

## Outcomes

`outcomes` is one entry per processed edit, in wave order, plus one entry per
preflight-held record. Each entry:

```json
{"index": 4, "node": "0xsvc", "attr": "phase",
 "reason": "precedence_winner", "value": "final", "edit_rank": 2}
```

`reason` is one of `commit_admit`, `precedence_winner`, `precedence_loser`,
`list_coalesce`, `policy_hold`, `preflight_hold`.

## Nodes

`nodes` is every node sorted by uid:

```json
{"uid": "0xsvc",
 "scalars": {"tier": "gold"},
 "lists": {"labels": [{"value": "vip", "lang": "en"}]},
 "facets": {"hwid": [{"key": "zone", "value": "z1"}]}}
```

## Atlas digest

`atlas_digest` is the lowercase SHA-256 hex of the UTF-8 bytes of the compact
JSON (keys sorted, separators `","` and `":"`, no whitespace) of:

```json
{"nodes": <N>, "outcomes": <O>, "schema_marks": <schema_marks>}
```

where each element of `<O>` has exactly the keys
`attr, edit_rank, index, node, reason, value`, and each element of `<N>` has
exactly the keys `facets, lists, scalars, uid` (list entries as
`{"lang","value"}`, facets as `{"key","value"}`). The order of outcomes and
nodes matches the atlas arrays.
