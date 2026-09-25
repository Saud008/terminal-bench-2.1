Revision-watch operators run the host-local relationwatchd control plane at `/usr/local/bin/relationwatchd`. Each offline ops pass admits relationship-tuple fixtures into SQLite, stages a revision snapshot, applies watch-cursor, caveat-tombstone, zed-token, stale-lag, and closure-invalidation gates, then publishes a sealed membership report only when those contracts hold. There is no live authorization cluster and no outbound network step. This is a system-administration host-local ops desk (admit → gate → seal). It is not a debugging exercise, software-engineering module-repair task, Go HTTP service rebuild, SpiceDB cluster ops drill, security product audit, or data-processing pipeline.

relationwatchd is built from the Go sources under `/app`. Bring the working baseline under `/app` (especially packages under `/app/internal/`) into compliance with the ops contracts below so seed, write, check, watch, and export match those documents. Evaluation rebuilds `/usr/local/bin/relationwatchd` from the sources under `/app` via `/app/scripts/verifier-rebuild.sh` before grading; replacing only the installed binary without aligning the sources will not pass. Do not use apt-get, pip install, or other network installs.

Ops contracts under `/app/docs/` define the enforceable invariants:

- `tuple-schema.md` — relationship write body and mutation outcomes
- `watch-export-schema.md` — filtered revision watch delivery, cursor advancement, and filtered_skips
- `zed-token-schema.md` — eight-byte revision tokens
- `revision-snapshot.md` — `/app/state/revision-snapshot.json` including recomputed `check_summaries`
- `check-contract.md` — live versus stale-snapshot membership evaluation
- `export-schema.md` — `/app/output/authz-report.json`

Each successful tuple mutation and namespace-prefix delete must refresh `/app/state/revision-snapshot.json` per `revision-snapshot.md` with live probe summaries for the documented `doc/plan` viewer subjects. Export reads that snapshot and writes `/app/output/authz-report.json` per `export-schema.md`. Runtime config is `/app/config/relationwatch.json`. Operator verbs and request bodies are described in the ops contracts under `/app/docs/` and `/app/docs/fixture-catalog.md`. Bundled fixtures live under `/app/fixtures`.

After policy-module edits under `/app/internal/`, leave `/usr/local/bin/relationwatchd` current. Do not edit `/app/docs/`, `/app/config/`, or `/app/fixtures/`.
