# Submission explanations — go-river-job-attempt-heartbeat-scheduler-repair

**Task folder:** tasks/go-river-job-attempt-heartbeat-scheduler-repair/
**Platform form only** — not in upload zip.
**Updated:** 2026-06-28T12:35:00Z

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is marked medium because riverbench couples five independent scheduler bugs across queue selection, exponential backoff, heartbeat lease refresh, poison caps, and SQLite lease cleanup. Contracts in scheduler-contract.md, lease-contract.md, and worker-api.md split the rules, so fixing dequeue order alone still leaves stale leases after ack, and fixing heartbeat alone still lets poison jobs requeue forever. Procedural seeding derives priorities and payloads from the seed string, which blocks hard-coded catalog answers. Partial-trap checks swap single corrected modules back into a broken tree and expect remaining defects to surface, punishing one-file patches that look complete on the happy path.

## Solution Explanation

The oracle replaces broken Go sources under internal/scheduler and internal/store with golden implementations, then rebuilds riverbench with go build. Queue selection must sort by lowest priority then lexicographic id, backoff must use attempt exponent only, heartbeat must refresh the requested job lease not the worker latest lease, poison must cap retries at max_attempts, and ack must delete lease rows. The store layer must expose lease lookup by job id so heartbeat and ack can enforce per-job ownership. Agents must preserve exported API surfaces on store.Store and the scheduler package so downstream callers and module-level rebuilds keep compiling.

## Verification Explanation

Pytest runs twenty behavioral cases after test.sh rebuilds riverbench with go build and serves the HTTP API on localhost. Tests drive worker claim, heartbeat, ack, fail, and admin seed endpoints through urllib while comparing dequeue order, backoff timestamps, lease tables, and poison state against an independent Python reference_scheduler module. Bundled fixture hashes are pinned so agents cannot edit contracts or catalogs. Frontier trap tests hot-swap single golden scheduler modules into an otherwise broken build and assert cross-module defects still fail, blocking shallow repairs that pass only the default integration path. Alternate VERIFIER_SEED values re-check procedural mutation so metadata cannot be memorized from one seed.
