The radiusproxy service under /app replays offline FreeRADIUS-style accounting JSONL captured at a proxy tier and materializes interim buffer flush order, session lineage, and SQLite ledger state for audit. Public replay bundles live under /app/fixtures/radius/ and the runtime config is /app/config/radiusproxy.json.

Repair the Go implementation under /app/internal/ so ingest and export honor /app/docs/radius-acct-contract.md, /app/docs/acct-packet-format.md, /app/docs/interim-interval-precedence.md, /app/docs/proxy-flush-queue.md, /app/docs/flush-snapshot-schema.md, and /app/docs/fixture-catalog.md. Ingest writes /app/state/acct-flush-snapshot.json and /app/state/acct-ledger.db. Export reads the staging snapshot only and writes /app/output/radius-acct-flush-report.json. CLI usage is in /app/README.md.

Do not edit /app/docs/, /app/fixtures/, /app/config/radiusproxy.json, or anything under /tests/. Run /app/scripts/reset-state.sh before local checks.
