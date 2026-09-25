# PATH mutation rules

Path mutations are collected in load_sequence order, then materialized:

Prepend stack:
- For each environment variable, prepends from later modules in load_sequence are applied closer to the front (left) of the final value
- When exporting path_mutations array, list prepends in load order (not final left-to-right order)

Append stack:
- Appends accumulate left-to-right in load_sequence order
- LD_LIBRARY_PATH append chains follow the same left-to-right accumulation rule documented for every append-capable variable

Final value for variable VAR:
- Start empty
- Apply prepend stack for VAR (leftmost prepend wins visually at front)
- Then apply append stack for VAR

The staging [path_final] section stores VAR|prepend_chain|append_chain using colon-separated segments.
