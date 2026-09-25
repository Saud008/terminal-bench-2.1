# Vet trace JSON

| Field | Type | Meaning |
|-------|------|---------|
| `workspace` | string | workspace directory name |
| `seed` | string | `--seed` argument |
| `ok` | bool | all vet rules satisfied |
| `error` | string | set when evaluation fails (cycles, closed, etc.) |
| `traces` | array | vet trace rows |

Each trace row:

| Field | Type | Meaning |
|-------|------|---------|
| `path` | string | vet rule path |
| `attr` | string | vet attribute (`default`, `required`, `optional`, `lineage`) |
| `lineage` | array of strings | `config.<id>`, full flattened embed chain, field leaf |
| `detail` | string | human-readable detail; for default disjunct traces use `default disjunct [opt1 opt2 ...]` |

When `ok` is false due to structural failure, `traces` may be empty and `error` must be set.
