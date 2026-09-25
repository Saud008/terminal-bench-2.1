# Export JSON

| Field | Type | Meaning |
|-------|------|---------|
| `workspace` | string | workspace directory name |
| `seed` | string | `--seed` argument |
| `values` | object | dotted-path → resolved value |
| `provenance` | array | optional-field provenance rows |

Provenance row:

| Field | Type | Meaning |
|-------|------|---------|
| `path` | string | dotted export path |
| `kind` | string | always `optional` in this task |
| `source` | string | `filename:line` from the export rule |

Every `export … optional` rule in the workspace must appear in `provenance`.
