# SQLite WAL segment reconciler

Shell toolchain that validates WAL frame checksums, records applied frames in `_wal_applied`, writes `/app/state/wal.stage`, and exports `/app/output/wal-report.json`.

See `/app/docs/cli.md` for subcommands and `/app/docs/invariants.md` for post-reconcile checks.
