# Submission explanations — pg-wal-archive-readiness-planner

**Task folder:** tasks/pg-wal-archive-readiness-planner/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task asks agents to implement the Bash walplan utility that plans PostgreSQL WAL archive restore readiness through ingest and plan stages. Contracts span WAL filename parsing, timeline history files, segment continuity across timelines, partial segment suffix handling, backup_label UTC start times, segment-clock end-time math, staging digest hashing, and restore planner JSON with exit codes. The instruction cites seven docs under /app/docs and requires plan to read staging segments_present rather than rescanning archive trees. Partial fixes pass bundled alpha fixtures but fail on gap continuity, partial-block restore rejection, timeline-switch history parsing, shuffle-label whitespace, and hidden TB3 archives that need TB3_CLOCK_ROOT for alternate segment clocks. Interactions between filesystem layout, PostgreSQL naming rules, and temporal restore constraints mean fixing one module leaves planner output wrong.

## Solution Explanation

The oracle copies golden Bash modules from solution patches into /app/lib and resets /app/state. Stage one walplan ingest writes /app/state/wal-archive.stage with segments_present, partial_files, timelines, and digest. Stage two walplan plan reads that snapshot only, applies segment-clock.json (or TB3_CLOCK_ROOT override), selects the latest complete segment whose end time is still less than or equal to the restore target, checks continuity gaps from staged segments, and emits sorted planner JSON. Key insight is export-only plan logic must not call select_restore_segment against the archive directory when staging already lists segments, and partial files must block restore when their segment number is on or before the selected segment on the same timeline.

## Verification Explanation

test.sh runs pytest against walplan via subprocess with an independent reference_walplan.py builder. Tests cover ingest staging snapshots, planner JSON equality, scan exit codes, gap and partial-block failure modes, staging-only plan behavior, TB3 hidden fixtures under /opt/verifier-fixtures, and partial module traps that swap broken copies from /opt/verifier-broken-walplan. Default cli.md paths /app/state/wal-archive.stage and /app/output/plan.json are exercised explicitly. Oracle patches nine golden lib modules. NOP on the shipped broken baseline scores zero.
