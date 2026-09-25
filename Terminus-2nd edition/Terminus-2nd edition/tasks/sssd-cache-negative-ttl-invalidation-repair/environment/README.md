# sssdcache

Offline SSSD cache negative TTL replay CLI.

## Commands

sssdcache ingest --ops /app/fixtures/ops --config /app/config/sssdcache.json writes /app/state/sssd-cache-snapshot.json and /app/state/sssd-cache.db.

sssdcache export --snapshot /app/state/sssd-cache-snapshot.json --output /app/output/sssd-cache-report.json reads the snapshot only.

Reset runtime state with /app/scripts/reset-state.sh before checks.

Contract docs live under /app/docs/.
