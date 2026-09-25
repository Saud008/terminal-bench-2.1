The harbor tug dispatch service under /app ingests AIS-style dispatch JSONL, persists assignments in SQLite, writes a staging snapshot to /app/state/ingest-snapshot.json, and exports a berth report to /app/output/berth-report.json.

Ingest and export no longer match the contract in /app/docs/berth-contract.md and /app/docs/export-format.md. Several documented behaviors are inconsistent between the CLI and the specs under /app/docs/.

Repair the Go service so tug-berth ingest and tug-berth export satisfy the docs, then verify with the usual CLI entrypoints documented in /app/README.md.
