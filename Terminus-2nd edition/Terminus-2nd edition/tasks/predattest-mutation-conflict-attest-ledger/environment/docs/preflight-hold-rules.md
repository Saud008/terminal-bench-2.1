# Preflight hold rules

Before a record binds identities or applies any edit, its `preconds` are
evaluated against the **live** graph — the state as it exists at the start of
the record, not the state the record itself would produce.

Each precond is `{"attr": <name>, "op": "eq", "value": <str>}` and is checked
against the **root node** (`config.root_node`, `0xroot`):

- the root node must have a scalar `attr`, and its value must equal `value`;
- a missing scalar fails the precond;
- any `op` other than `eq` fails the precond.

If **any** precond fails, the whole record is **held**: none of its edits are
bound or applied, and it contributes a single outcome with reason
`preflight_hold` (with empty `node`/`attr`/`value` and `edit_rank` 0). Each
held record increments `held_records`.

Because evaluation is against live state only, a record whose own edit would
have satisfied its precond is still held.
