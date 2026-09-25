The riverbench worker scheduler at /app/cmd/riverbench serves a job-attempt API backed by a SQLite lease table, but its behavior disagrees with /app/docs/scheduler-contract.md, /app/docs/worker-api.md, and /app/docs/lease-contract.md.

Repair the Go implementation under /app/internal/ so worker claim, heartbeat, ack, fail, and the admin hooks documented in /app/docs/worker-api.md match every contract for claim ordering, lease invariants, and temporal backoff on bundled catalogs and procedural seeds.

The environment has no outbound network access. Rebuild and use:

go build -mod=readonly -o /usr/local/bin/riverbench ./cmd/riverbench
riverbench serve --listen 127.0.0.1:8092 --config /app/config/scheduler.json

Do not edit /app/docs/, /app/fixtures/, or /tests/.

Do not add or rename exported methods on store.Store; repair lease and job persistence using the existing exported store API.

Do not add or rename exported types, vars, or functions anywhere under /app/internal/scheduler/; keep the existing scheduler package API unchanged so internal/api callers and any single-module rebuild of scheduler sources keep compiling.
