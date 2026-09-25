# Playfield path planner export contracts

## validate export

| Field | Type | Meaning |
|-------|------|---------|
| `mesh_id` | string | Playfield board id |
| `seed` | u64 | `--seed` playtest argument |
| `ok` | bool | `true` when no validation errors |
| `errors` | string[] | Human-readable failures |
| `islands` | u32 | Walkable connected zones |
| `links_checked` | u32 | Off-mesh jump links validated |
| `portals_checked` | u32 | Portal rows validated |

## path export

| Field | Type | Meaning |
|-------|------|---------|
| `status` | string | `ok` or `unreachable` |
| `cost_q16` | i32 | Total route cost in Q16.16 fixed point |
| `path` | string[] | Ordered cell ids |

Route costs use Q16.16 integer accumulation, not float truncation.
