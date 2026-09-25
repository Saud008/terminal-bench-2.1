The session replay ledger at /app replays captured execution reports from protocol capture files into SQLite and exports net positions per symbol. It should ingest session files, persist executions, write a canonical ingest staging snapshot under /app/state/, and export positions to /app/output/positions.json.

Ingest and export currently disagree with the contracts in the documentation under /app/docs/. Valid bundled session files under /app/fixtures/ are rejected at ingest because body-length validation is wrong. When ingest does succeed, staging message order, export net quantities on cancels, VWAP, and duplicate ClOrdID replay handling are still incorrect.

Implement the Go service so the ledger CLI ingest and export subcommands behave as documented. See /app/docs/fix-checksum.md, /app/docs/replay-ordering.md, /app/docs/staging-format.md, /app/docs/idempotency.md, and /app/docs/export-format.md for field rules.

After your changes, /app/bin/fix-ledger ingest --session-dir <dir> --db /app/state/ledger.db must write /app/state/ingest-staging.json and /app/bin/fix-ledger export --db /app/state/ledger.db --out /app/output/positions.json must produce the JSON schema in /app/docs/export-format.md.
