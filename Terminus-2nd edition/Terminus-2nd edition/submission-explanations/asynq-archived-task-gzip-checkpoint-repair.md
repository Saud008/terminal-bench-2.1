# Submission explanations - asynq-archived-task-gzip-checkpoint-repair

**Task folder:** tasks/asynq-archived-task-gzip-checkpoint-repair/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-28T03:23:00Z

**Category note:** Zip metadata uses `system-administration` (host local archctl queue archive retention control plane). Prefer that lane on the platform form. Do not set debugging,software-engineering,data-processing,or security.

> Agent scaffold only - rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Hard because archctl must flush gzip footers before index sizes,keep last member wins on duplicate ids,preserve archived priority apart from retry,purge with UTC skew,and export from the staging snapshot while the baseline breaks those edges across packages.Held out duplicate and priority traps plus partial member cases stop one file patches from clearing the suite.

## Solution Explanation

The oracle replaces writer,import,purge,publish,and snapshot modules with footer flush,last member wins restore,UTC purge skew,and staging backed manifest export.Rebuild archctl after the copies and reset queue state so seed archive restore matches the docs.

## Verification Explanation

The verifier rebuilds archctl then runs pytest on seed archive restore purge and manifest against an independent reference walker.Held out fixtures stage only at grade time and structural checks block empty stubs while NOP scores zero and oracle scores one.
