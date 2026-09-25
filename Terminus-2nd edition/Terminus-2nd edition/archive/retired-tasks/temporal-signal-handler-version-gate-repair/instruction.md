Build a Temporal-style signal replay export capability on the working /app baseline so temporal-signal-replay produces reproducible workflow history artifacts from scenario ingest through staging snapshot and export.

Implement the Go modules under /app/internal/ against the contracts in /app/docs/version-gate.md, /app/docs/handler-ack-order.md, /app/docs/staging-snapshot.md, /app/docs/export-history-schema.md, /app/docs/fixture-catalog.md, and /app/docs/cli-errors.md. Export must read the staged snapshot at /app/state/signal-snapshot.json and must not re-walk scenario signals using ad-hoc ordering or filters.

Keep existing exported function names and signatures stable across packages. Do not add new exported symbols that other internal packages must call, and do not refactor /app/internal/replay to depend on newly introduced helpers, because verifier partial-module checks restore broken baselines per file.

CLI usage:

temporal-signal-replay export --scenario /app/fixtures/scenarios/01-baseline.json --output /app/output/signal-history-export.json
