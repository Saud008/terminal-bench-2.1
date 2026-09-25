# Libtool manifest schema

`/app/output/libtool-manifest.json` is one JSON object:

| Field | Type | Meaning |
|-------|------|---------|
| `manifest_version` | number | Always `1` |
| `project_root` | string | Absolute project path passed to the tool |
| `stats` | object | Counters described below |
| `libraries` | array | One entry per discovered `.la` file |
| `broken_edges` | array | Cycle edges removed (may be empty) |

### `stats`

| Field | Meaning |
|-------|---------|
| `la_files` | Count of `.la` files discovered |
| `cycles_broken` | Number of edges removed while breaking cycles |
| `rpaths_deduped` | Total duplicate rpath tokens removed across all libraries |

### Library entry

| Field | Type | Meaning |
|-------|------|---------|
| `id` | string | Basename without `.la` (e.g. `libcore`) |
| `la_relpath` | string | Path relative to `project_root` using `/` separators |
| `installed` | boolean | From `.la` `installed` field |
| `resolve_dir` | string | Directory chosen by path resolution rules |
| `dependency_order` | string[] | Direct in-project dependency ids from `dependency_libs` only (depth 1), topologically sorted among themselves (dependencies before dependents). Omit transitive dependencies. When a direct edge from this library to a dependency appears in `broken_edges`, omit that dependency id from this array entirely. When multiple ids are ready, emit the lexicographically smallest id first and resort the ready set after each step. |
| `rpath` | string[] | Deduped rpath directories in first-seen order |
| `shared_name` | string | Shared soname or empty |
| `static_fallback` | string | Static archive name or empty |

Libraries are sorted by `id` ascending in the export array.

## Exit codes

| Code | When |
|------|------|
| 0 | Manifest written |
| 1 | I/O or JSON error |
| 2 | Missing project directory or no `.la` files |
