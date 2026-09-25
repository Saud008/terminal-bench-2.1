The Asynq-style archived task tool under /app stores pending work in SQLite at /app/work/queue.db, writes gzip member bundles under /app/work/archives/, and exposes archctl at /usr/local/bin/archctl with seed, archive, restore, purge, and manifest subcommands described in /app/docs/cli-surface.md.

Archive creation must follow /app/docs/archive-format.md and /app/docs/checkpoint-index.md: each gzip member footer must be flushed before the index checkpoint records member size and file offset. Restore must follow /app/docs/restore-import.md (dedupe duplicate task IDs across members, preserve archived priority separate from retry count). Retention purge must follow /app/docs/retention-purge.md using UTC archived timestamps. Queue priority semantics are defined in /app/docs/queue-priority.md.

During archive, write the staging snapshot at /app/state/archive-snapshot.json per /app/docs/checkpoint-index.md. After restore, manifest export must land at /app/output/<seed>-<scenario>-manifest.json using the contract in /app/docs/restore-import.md and the staging snapshot, not a live queue scan alone.

Repair the Go packages under /app/internal/ and rebuild archctl from /app. Do not edit /app/docs/, /app/config/, or /app/fixtures/.
