# Submission explanations — freeradius-proxy-acct-interim-buffer-flush-repair

**Task folder:** tasks/freeradius-proxy-acct-interim-buffer-flush-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is hard because the agent must repair five interacting Go modules so radiusproxy replays FreeRADIUS-style accounting JSONL into a staged flush snapshot and SQLite ledger, then exports a report from staging only. Contract rules span six docs: Acct-Interim-Interval beats Session-Timeout for flush timing, NAS reboots start a new lineage when Acct-Unique-Session-Id changes, interim batches flush by session_start_ts then seq rather than arrival order alone, and Stop forces pending interim rows out even when the interval has not elapsed. Ingest must write /app/state/acct-flush-snapshot.json and checkpoint WAL on /app/state/acct-ledger.db, while export must never reread JSONL logs. Fixing interval precedence or queue ordering alone still fails cumulative replay, flush-order SQLite checks, or export count invariants because dedupe, persistence, and staging publish must all agree.

## Solution Explanation

The oracle copies golden interval.go, dedupe.go, queue.go, sqlite.go, and stage.go into /app/internal/, rebuilds radiusproxy with go build -mod=vendor, and resets state. EffectiveInterimSec prefers Acct-Interim-Interval over Session-Timeout; session dedupe keys on nas_id, Acct-Session-Id, and Acct-Unique-Session-Id and treats a Start with a new unique id as a reboot lineage without merging octets. The proxy queue enqueues Interim-Update rows, flushes due batches sorted by session_start_ts and seq, and drains pending interim on Stop while updating last_flush_ts and stats counters. SQLite persist writes session_ledger and flush_ledger then runs PRAGMA wal_checkpoint(FULL); staging captures the snapshot body that export Publish reads to emit radius-acct-flush-report.json with sessions_completed counting stopped sessions only and interim_flushed taken from snapshot stats.

## Verification Explanation

Pytest rebuilds the Go CLI in test.sh, runs radiusproxy ingest and export via subprocess, and compares output to an independent reference_validator.py replay of the same JSONL and config. Six public fixtures under /app/fixtures/radius/ cover baseline accounting, interim precedence, NAS reboot lineage, flush ordering, interim storms, and stop-with-pending-interim; dedicated tests assert snapshot equality, WAL checkpoints, SQLite flush_ledger row order, export-only-from-snapshot behavior, and correct sessions_completed versus interim_flushed fields. A hidden reboot-interim-storm capture under /tests/fixtures-hidden/ and optional TB3_RADIUS_DIR override block shortcuts that only pass bundled logs. Parametrized single-module golden swaps for interval, dedupe, queue, sqlite, stage, and rollup prove one-file patches cannot satisfy full cumulative reference export.
