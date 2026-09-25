# navmeshctl export contracts

## validate export

| Field | Type | Meaning |
|-------|------|---------|
| `mesh_id` | string | Bundle id |
| `seed` | u64 | `--seed` argument |
| `ok` | bool | `true` when no validation errors |
| `errors` | string[] | Human-readable failures |
| `islands` | u32 | Walkable connected components |
| `links_checked` | u32 | Off-mesh links validated |
| `portals_checked` | u32 | Portal rows validated |

## path export

| Field | Type | Meaning |
|-------|------|---------|
| `status` | string | `ok` or `unreachable` |
| `cost_q16` | i32 | Total path cost in Q16.16 fixed point |
| `path` | string[] | Ordered cell ids |

Path costs use Q16.16 integer accumulation, not float truncation.
