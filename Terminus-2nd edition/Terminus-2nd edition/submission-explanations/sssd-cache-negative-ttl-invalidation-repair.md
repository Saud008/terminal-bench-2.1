# Submission explanations — sssd-cache-negative-ttl-invalidation-repair

**Task folder:** tasks/sssd-cache-negative-ttl-invalidation-repair/
**Platform form only** — not in upload zip.

## Difficulty Explanation

This task is hard because sssdcache replay must keep negative TTL refresh, domain-scoped cache keys, nested group invalidation, export filtering, and same-timestamp ordering aligned across eight /app/docs contracts. Agents often fix lookup_miss TTL or export filtering in isolation while replay_engine.go still applies the wrong kind priority at equal ts and seq, which breaks invalidate and lookup_hit ordering traps. Explicit invalidate must remove both positive and negative rows without conflating group_invalidations counters with explicit_invalidation stats. Domain suffix canonicalization must lower-case only the domain portion of each key so principals with identical display names in different domains stay distinct. Partial fixes pass a few bundled fixtures but fail /opt/verifier-fixtures TB3 bundles that combine nested churn, same-ts traps, and invalidate poison scenarios.

## Solution Explanation

The oracle installs corrected cache_key.go, cache_negative.go, replay_engine.go, group_nested.go, store_sqlite.go, and export_stage.go, then rebuilds sssdcache with go build -mod=vendor. Ingest replays JSONL operation logs in documented order, writes /app/state/sssd-cache-snapshot.json, and persists active negatives to /app/state/sssd-cache.db with a WAL checkpoint counter. Export reads the snapshot only and filters active_negatives using evaluated_at_ms so expired negatives never appear in /app/output/sssd-cache-report.json. Nested group membership changes invalidate transitive users when nested_invalidation is true, while explicit invalidate kind clears named principals only. lookup_hit removes negative rows per negative-ttl-contract and increments lookup_hit stats without skipping same-ts tie-break rules.

## Verification Explanation

Eighteen pytest functions rebuild the Go binary in test.sh and drive sssdcache ingest and export through subprocess on every run. An independent reference_cache module recomputes expected snapshot and export JSON from the same fixtures and /app/config/sssdcache.json, preventing hard-coded answers. Bundled fixtures under /app/fixtures/ops/ cover TTL refresh, domain keys, same-ts ordering, nested groups, lookup_hit, and explicit invalidate behavior. /opt/verifier-fixtures supplies nested churn, TB3 same-ts invalidate versus lookup_hit ordering, and invalidate poison traps that fail when only the obvious bundled file is patched. Tests assert canonical artifact paths, SQLite active-negative filtering, snapshot-only export, and SSSD_DOMAIN_SUFFIX overrides.
