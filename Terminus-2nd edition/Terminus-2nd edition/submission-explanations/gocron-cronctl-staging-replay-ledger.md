# Submission explanations - gocron-cronctl-staging-replay-ledger

**Task folder:** tasks/gocron-cronctl-staging-replay-ledger/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-29T15:15:00Z

> Agent scaffold only - rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Hard because cronctl must keep staging digests, DST single-fire gates, per-instant singleton coalesce, tick-window fires under TB3_CLOCK_START and TB3_TICK_MS, absolute-only TB3_FIXTURE_DIR, per-job leases, and sealed export aligned while the baseline breaks those edges across packages. Held-out packs via absolute fixture-dir overrides plus second-run generation gates stop partial fixes from clearing the suite.

## Solution Explanation

The oracle replaces timezone resolve, cron fire expand, staging snapshot, singleton guard, per-job lease release, run tracking, controllable clock, absolute fixture-root main, ordered SQLite list, replay tick windows with per-instant coalesce, and export gates with contract-aligned behavior. Rebuild cronctl after the copies and keep generation bump plus panic lease release on the replay path.

## Verification Explanation

The verifier rebuilds cronctl then runs pytest on load, replay, and export against an independent schedule reference from protected `/tests/data` fixtures (not agent-writable `/app/fixtures`). Held-out scenarios stage only at grade time under `/opt/verifier-fixtures`, and row-level SQLite checks enforce documented `fired_at_ms, job_id` ordering while NOP scores zero and oracle scores one.
