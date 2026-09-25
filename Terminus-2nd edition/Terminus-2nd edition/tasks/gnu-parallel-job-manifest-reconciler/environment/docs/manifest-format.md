# job.manifest.json staging schema

Written by `par-chain stage` to `/app/state/job.manifest.json`.

```json
{
  "exit_histogram": {"0": 2},
  "job_count": 2,
  "par_files_parsed": 2,
  "peak_concurrency": 1
}
```

| Field | Meaning |
|-------|---------|
| `job_count` | Data rows in the joblog (header excluded) |
| `par_files_parsed` | Count of `*.par` files read under `--par-dir` |
| `peak_concurrency` | Maximum simultaneous running jobs from `.par` intervals (see invariants) |
| `exit_histogram` | Map of exit code string → count using **authoritative `.par` exit`** when a `.par` exists; otherwise joblog Exitval |

The manifest must be written **only after** every `*.par` file has been parsed. Keys are sorted. Trailing newline required.
