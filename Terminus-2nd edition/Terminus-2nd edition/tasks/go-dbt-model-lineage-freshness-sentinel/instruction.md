Platform operators run the host-local dbtsent manifest-scan control plane at /usr/local/bin/dbtsent. Each offline ops pass admits seed-scoped manifest packs under /app/fixtures/bundles/, stages a pack-bound checkpoint at /app/state/manifest-checkpoint.json, enforces age-window gates and disabled-upstream dependency gates, walks exposure dependency closures, and publishes a digest-bound alert report at the caller --output path under /app/output/. There is no remote cluster or live scheduler. This is a system-administration host-local checkpoint ops control plane; keep ingest staging, scan admission order, dependency gates, and sealed export aligned. It is not a generic service repair exercise or a Go CLI rebuild / pytest harness.

Primary artifacts:

  /app/state/manifest-checkpoint.json — seed-scoped checkpoint from ingest
  /app/work/freshness-scans.db — SQLite store of active scan rows
  /app/output/<seed>-<bundle>-freshness-report.json — digest-bound alert report path

Ops contracts cover warn/error age windows, DISABLED_UPSTREAM gates, exposure depends_on closure, SQLite scan replacement, and audit_digest field order. Operator verbs and pack roots follow /app/docs/manifest-checkpoint-schema.md, /app/docs/model-dag-traversal.md, /app/docs/source-freshness-windows.md, /app/docs/disabled-model-handling.md, /app/docs/exposure-dependency-closure.md, /app/docs/sentinel-database-schema.md, /app/docs/alert-export-contract.md, /app/docs/freshness-scan-admission-order.md, /app/docs/tb3-overlay-packs.md, and /app/docs/manifest-scan-ops-contract.md.

Alert message strings are part of audit_digest. Use the exact templates in /app/docs/alert-export-contract.md (SOURCE_STALE: `source stale {N} min`; DISABLED_UPSTREAM: `depends on disabled {unique_id}`; EXPOSURE_EMPTY: `exposure has no model refs`). Seed-scoped unique_ids use the FNV-1a suffix transform in /app/docs/manifest-checkpoint-schema.md. exposure_refs includes disabled models; model_order does not.

Subcommands:

  dbtsent ingest --seed <seed> --bundle <name>
  dbtsent evaluate scan --seed <seed> --bundle <name>
  dbtsent export alerts --seed <seed> --bundle <name> --output <path>

dbtsent ingest must write the checkpoint at /app/state/manifest-checkpoint.json. dbtsent evaluate scan must apply scan admission order and persist active scan rows to /app/work/freshness-scans.db. dbtsent export alerts may publish digest-bound reports only from that checkpoint plus active scan rows.

Bundled pack names are core-lineage, freshness-mixed, disabled-refs, and exposure-depth. Pack inventory appears in /app/docs/manifest-pack-catalog.md. Hidden overlay pack tb3-bias-overlay loads tb3-bias-overlay.json from TB3_BUNDLE_DIR per /app/docs/tb3-overlay-packs.md.

Install /usr/local/bin/dbtsent from the Go sources under /app. The verifier rebuilds that binary with `go build -mod=readonly` before grading, so keep fixes in Go within the existing go.mod dependency set; a non-Go replacement binary is overwritten and will not be graded.

The internal decoy materializer module is not on the ingest, evaluate, or export ops path. Do not edit /app/docs/, /app/config/, or /app/fixtures/.
