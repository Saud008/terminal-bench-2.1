# parallel-export.json export schema

Written by `par-chain export`.

```json
{
  "cpu_seconds": 0.0,
  "exit_histogram": {"0": 2},
  "failed_exit_count": 0,
  "job_count": 2,
  "peak_concurrency": 1
}
```

| Field | Meaning |
|-------|---------|
| `job_count` | `SELECT COUNT(*) FROM jobs` in manifest.db after reconcile |
| `peak_concurrency` | Same definition as staging manifest — interval overlap peak, not `MAX(slot)` |
| `cpu_seconds` | Sum over all `.par` files of `(utime_jiffies + stime_jiffies) / USER_HZ` with `USER_HZ=100` — **not** max `wall_sec` |
| `exit_histogram` | From reconciled database exit values (post `.par` merge) |
| `failed_exit_count` | Jobs whose exitval is not `0` (exit `127` counts as failure) |

Keys are sorted. Trailing newline required.
