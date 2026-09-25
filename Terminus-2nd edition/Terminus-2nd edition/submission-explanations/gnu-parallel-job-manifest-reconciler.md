# Submission explanations — gnu-parallel-job-manifest-reconciler

**Task folder:** tasks/gnu-parallel-job-manifest-reconciler/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task is medium difficulty because the par-chain pipeline must keep GNU parallel joblog parsing, per-job .par profiler merge, SQLite persistence, staging JSON, and export summaries aligned across five /app/docs contracts at once. Agents often fix peak concurrency by taking MAX(slot) or the highest slot id seen, which passes simple runs but fails when three jobs overlap while using slots 4, 1, and 2. Exit code 127 is another trap: the baseline treats it as success, so failed_exit_count stays zero even when the histogram shows a 127 bucket. Export cpu_seconds must sum (utime_jiffies + stime_jiffies) / 100 across every .par file, not the largest wall_sec, and staging exit_histogram must use authoritative .par exit values after the full par directory scan rather than raw joblog Exitval columns. Partial fixes on stage.sh or export.sh alone leave reconcile idempotency broken or manifest.db histograms out of sync with job.manifest.json.

## Solution Explanation

The oracle replaces joblog.sh, slots.sh, exitagg.sh, stage.sh, and export.sh under /app so par-chain reconcile, stage, and export follow the documented contracts. Reconcile loads joblog rows with INSERT OR IGNORE so a second pass does not duplicate seq values, then merge_par_into_db applies .par timing and exit overrides. Peak concurrency uses a sweep over start_epoch and end_epoch intervals from all .par files instead of MAX(slot). Staging writes job.manifest.json only after counting par files and building manifest_exit_histogram, which prefers .par exit when present. Export reads reconciled exitval from manifest.db, counts exit 127 as a failure, computes peak from interval overlap in the par directory, and sets cpu_seconds via par_cpu_seconds_total before writing sorted JSON with a trailing newline.

## Verification Explanation

Seven pytest functions drive /app/bin/par-chain reconcile, stage, and export through subprocess on every run after resetting /app/state/manifest.db and job.manifest.json. An independent reference_parallel module parses the same joblog and .par inputs, simulates interval-overlap peak concurrency, jiffies CPU totals, authoritative exit histograms, and SQLite row counts so answers cannot be hard-coded. Bundled fixtures under /app/fixtures/seed cover end-to-end manifest and export fields including a seed run with exit 127 in the histogram. Synthetic runs under pytest tmp_path isolate peak overlap when MAX(slot) would be 4 but three jobs overlap, exit 127 failure counting, cpu_seconds summing jiffies instead of wall time, idempotent second reconcile, and staging histograms that reflect .par exit overrides when joblog Exitval differs.
