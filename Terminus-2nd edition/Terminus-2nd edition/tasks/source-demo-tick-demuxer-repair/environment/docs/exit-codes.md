# demo-index exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Usage error, missing demo, bad magic/version, or malformed packet mid-stream |
| 2 | Partial packet at EOF (truncated body) |

`demo-index probe --demo <path>` parses a single file and returns the same codes without writing export JSON.
