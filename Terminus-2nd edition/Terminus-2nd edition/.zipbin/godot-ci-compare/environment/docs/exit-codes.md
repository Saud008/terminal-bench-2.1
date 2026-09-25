# Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General runtime or I/O error |
| 2 | UID graph cycle detected (`uid_graph_ok` would be false) |

When exit code is 2, still write the export JSON if `--export` was provided.
