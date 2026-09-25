# Post-reconcile invariants

After `par-chain reconcile`, `stage`, and `export` on joblog `J` and par directory `P`:

1. `SELECT COUNT(*) FROM jobs` equals the number of data rows in `J`.
2. `SELECT COUNT(DISTINCT seq) FROM jobs` equals `SELECT COUNT(*) FROM jobs` (no duplicate seq on re-reconcile).
3. Running `par-chain reconcile` a second time with the same inputs completes without error and does not increase job row count.
4. `job.manifest.json` field `par_files_parsed` equals the number of `*.par` files in `P`.
5. `exit_histogram` in `job.manifest.json` matches histogram built from `.par` `exit=` when present, else joblog Exitval — **after** all `.par` files are parsed.
6. `peak_concurrency` is the maximum count of jobs whose `[start_epoch, end_epoch)` intervals overlap at any instant; not `MAX(slot)` across files.
7. `parallel-export.json` `cpu_seconds` equals the summed jiffies CPU time from all `.par` files divided by 100.
8. `failed_exit_count` treats exit code `127` as a failure (not success).
9. Export `exit_histogram` matches `SELECT exitval FROM jobs` after `.par` merge.

Operators may query invariants directly with `sqlite3 /app/state/manifest.db`.
