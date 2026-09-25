# Fixture wave catalog

A mutation wave is a JSONL stream; each line is one **commit record** applied
in file order to a shared fleet graph. The graph starts with a single root
node whose uid is `config.root_node` (`0xroot`) carrying scalar
`state = config.root_state` (`active`).

## Record schema

```json
{
  "commit_index": 3,
  "preconds": [{"attr": "state", "op": "eq", "value": "active"}],
  "edits": [
    {"node": "0xsvc", "attr": "tier", "value": "gold", "edit_rank": 2},
    {"node": "_:x", "attr": "role", "value": "leader", "edit_rank": 1,
     "bind": true,
     "bind_on": [{"attr": "hwid", "value": "h1",
                  "facets": [{"key": "zone", "value": "z1"}]}]},
    {"node": "0xsvc", "attr": "labels", "value": "vip", "lang": "en",
     "multi": true, "edit_rank": 4, "facets": []}
  ],
  "schema_marks": ["labels"],
  "commit": true
}
```

- `commit_index` — integer identity of the record (echoed into outcomes and
  `last_commit_index`).
- `preconds` — `@if` conditions checked by the preflight gate.
- `edits` — proposed writes. `node` is a concrete uid (e.g. `0xsvc`) or a
  blank node label (`_:name`). `attr`/`value` are strings. `edit_rank` is the
  precedence key. `multi: true` marks a list-valued edit; `lang` tags a list
  entry. `facets` is a list of `{key,value}` on a scalar attr. `bind` +
  `bind_on` request identity binding of a blank node.
- `schema_marks` — schema epoch names this record appends when it commits.
- `commit` — when false the record aborts (see schema-bump-abort).
- `wall_time_ms`, if present on an edit, is advisory only and must never
  affect any decision.

## Public waves under `/app/fixtures/waves/`

- `wave-alpha.jsonl` — policy holds (`drain_token`, `raw_secret`) plus the
  near-miss attr `drain_token_scope = "west"` that must pass through.
- `wave-bravo.jsonl` — one same-attr precedence conflict on the root node's
  `phase`: `phase = "draft"` at `edit_rank` 1 (with a large, misleading
  `wall_time_ms`) versus `phase = "final"` at `edit_rank` 2. The higher rank
  wins, so `final` is the `precedence_winner` and `draft` is the
  `precedence_loser`; the root ends with `phase = "final"`.
- `wave-charlie.jsonl` — a preflight hold, an aborted schema bump
  (`ghost_mark`), and a distinct-lang list (`vip`/`en` and `vip`/`fr`).
- `wave-merged.jsonl` — one wave that surfaces every outcome reason.

Evaluation may also point at waves outside `/app/fixtures/`.
