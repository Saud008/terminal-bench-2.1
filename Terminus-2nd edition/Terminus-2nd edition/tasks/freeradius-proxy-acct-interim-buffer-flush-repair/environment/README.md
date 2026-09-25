# radiusproxy

Offline FreeRADIUS proxy accounting interim buffer replay CLI.

## Commands

radiusproxy ingest --logs /app/fixtures/radius --config /app/config/radiusproxy.json writes /app/state/acct-flush-snapshot.json and /app/state/acct-ledger.db.

radiusproxy export --snapshot /app/state/acct-flush-snapshot.json --output /app/output/radius-acct-flush-report.json reads the snapshot only.

Reset runtime state with /app/scripts/reset-state.sh before checks.

Contract docs live under /app/docs/.
