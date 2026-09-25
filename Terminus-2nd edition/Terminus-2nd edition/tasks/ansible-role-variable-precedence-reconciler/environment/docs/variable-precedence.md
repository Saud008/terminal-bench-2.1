# Variable precedence contract

`ansible-var-merge resolve` materializes the effective variable mapping for one inventory host. Layers are applied from **lowest** precedence to **highest**. When two layers define the same key, the later layer wins unless hash merge rules apply.

## Layer stack (low → high)

| Rank | Layer | Source |
|------|-------|--------|
| 1 | Role defaults | `roles/<role>/defaults/main.yml` per playbook role order |
| 2 | Inventory group_vars | `group_vars/all.yml`, then each group membership file in ascending group name order |
| 3 | Inventory host_vars | `host_vars/<hostname>.yml` |
| 4 | Role vars | `roles/<role>/vars/main.yml` per playbook role order |
| 5 | include_vars | Playbook manifest entries sorted by ascending `depth` |
| 6 | Playbook vars | `vars` mapping in the playbook manifest |
| 7 | Extra vars | `--extra-vars` file when provided |

## Inventory rules

- A host receives `group_vars/all.yml` plus one file per direct inventory group listed in `hosts.ini`.
- Group files are merged in **ascending** group name order before host vars are applied.
- Host vars always override group vars for scalar keys.

## Role rules

- For each role listed in the playbook, merge defaults before vars so role vars override defaults.

## Hash behaviour

- `hash_behaviour: replace` (default): each layer performs a shallow mapping update.
- `hash_behaviour: merge`: when both the accumulated mapping and the incoming layer value for a key are mappings, merge recursively; otherwise replace the key.

## Output

`resolve` writes JSON with `host`, `seed`, and `merged` keys. The `seed` argument is echoed verbatim and does not alter precedence.
