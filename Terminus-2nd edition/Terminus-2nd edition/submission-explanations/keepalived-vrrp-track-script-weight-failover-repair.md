# Submission explanations — keepalived-vrrp-track-script-weight-failover-repair

**Task folder:** tasks/keepalived-vrrp-track-script-weight-failover-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is marked hard because agents must repair nine cooperating Bash library modules that drive the kv-sim VRRP track-script replay pipeline, not a single obvious script. Effective priority depends on max(priority_floor, base_priority plus active weights), but the broken weight module clamps the floor before adding weights, so combined demotions and recovery scenarios disagree with the contract in weight-priority.md. Simultaneous fall events must activate every qualifying track in config order, yet the race helper only keeps one winner. Replay idempotency, advert_seq reset on MASTER demotion, the notify barrier before export, and atomic publish with export-ready markers are split across replay, advert, notify, and export modules, so partial fixes still fail hidden dual-track fixtures or leave vrrp-state.json.tmp behind. A second config-check subcommand must parse keepalived.sample.conf, map chk_ scripts to vrrp.json, and execute each track script with real exit codes.

## Solution Explanation

The oracle replaces all nine golden kv_*.sh modules under /app/lib and runs reset-state before verification. Weight computation uses max(floor, base + sum(active weights)) and recomputes after rise clears a track. The race module activates every candidate that crossed fall in config array order. Replay skips duplicate event_id lines, advert bumps only while role stays MASTER and resets to zero on demotion, and export waits until notify_complete before writing. Durable publish writes vrrp-state.json.tmp, fsyncs, renames into place, fsyncs again, and records the basename in /app/state/export-ready. Staging snapshot and manifest capture applied_event_ids plus SHA256 digests of the raw events file and snapshot bytes. Config-check walks keepalived track_script names, runs each script path once, and emits tracks_checked, scripts_run, and all_scripts_ok.

## Verification Explanation

Pytest drives kv-sim replay and config-check through subprocess CLI calls after reset-state, comparing full staging snapshots and published graphs to an independent reference_vrrp.py implementation. Seven bundled JSONL fixtures cover single fail, priority floor clamp, advert reset, notify ordering, recovery rise, dual-track race, and duplicate event_id idempotency. Hidden traps include a verifier-only dual-track stream under /opt/verifier-fixtures/events and a seeded event stream keyed by VERIFIER_SEED so catalog memorization cannot pass. Behavioral tests assert non-zero exit on missing input, notify.done and export-ready side effects, manifest SHA256 binding, config-report parity with three executed track scripts, and absence of temporary export sidecars. Anti-cheat compares entire JSON structures rather than isolated scalar fields.
