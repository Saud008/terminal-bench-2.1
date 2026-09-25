The GNU parallel manifest toolchain at `/app` ingests a `--joblog` TSV and companion `.par` profiler logs from a run directory, persists reconciled job rows in `/app/state/manifest.db`, writes a staging snapshot at `/app/state/job.manifest.json`, and exports a summary report.

Reconcile, staging, and export currently disagree with `/app/docs/joblog-format.md`, `/app/docs/parlog-format.md`, `/app/docs/manifest-format.md`, `/app/docs/export-format.md`, and the invariants in `/app/docs/invariants.md`. Bring the shell modules under `/app` in line with those documents so `/app/bin/par-chain` behaves as specified. A sample joblog and `.par` directory ship at `/app/fixtures/seed/` for local smoke runs.

Example:

```text
/app/bin/par-chain reconcile --joblog /app/runs/batch/joblog.tsv --par-dir /app/runs/batch/par
/app/bin/par-chain stage --joblog /app/runs/batch/joblog.tsv --par-dir /app/runs/batch/par
/app/bin/par-chain export --joblog /app/runs/batch/joblog.tsv --par-dir /app/runs/batch/par --out /app/output/parallel-export.json
```
