Library operators run the host-local holdfairctl hold-queue fairness control plane at /app/bin/holdfairctl. Each offline ops pass mounts a scenario SQLite database, stages a hold-queue rollup digest, applies suspension-window, priority-tier, and pickup-branch routing gates, then publishes a sealed assignment atlas only from a committed reconcile pass. There is no remote ILS or consortial API and no outbound network step. This is a system-administration host-local ops desk (admit → gate → seal). It is not a debugging exercise, software-engineering module-repair task, build-and-dependency-management exercise, or data-processing pipeline.

holdfairctl is built from the Go sources under /app. Bring the working baseline under /app (especially packages under /app/internal/) into compliance with the ops contracts below so mount, rollup, reconcile, and export match those documents. Evaluation rebuilds /app/bin/holdfairctl from the sources under /app via /app/scripts/verifier-rebuild.sh before grading; replacing only the installed binary without aligning the sources will not pass. Do not use apt-get, pip install, or other network installs.

Ops contracts under /app/docs/ define the enforceable invariants:

- /app/docs/cli-surface.md — verb order and CLI defaults
- /app/docs/scenario-sqlite-contract.md — mount layout for active-library.db
- /app/docs/hold-rollup-contract.md — /app/state/hold-queue-rollup.json schema fields
- /app/docs/suspension-window-contract.md — inclusive suspension calendar admission
- /app/docs/priority-tier-contract.md — priority rank ordering
- /app/docs/copy-routing-contract.md — pickup_branch_id preference before interbranch transfer
- /app/docs/run-seal-contract.md — reconcile_pass advancement rules
- /app/docs/assignment-atlas-contract.md — sealed export schema fields

holdfairctl mount-library-db --scenario NAME [--fixture-dir PATH] must materialize /app/state/active-library.db and record scenario metadata at /app/state/scenario-active.json. holdfairctl compose-rollup --scenario NAME must write /app/state/hold-queue-rollup.json with the rollup digest required by /app/docs/hold-rollup-contract.md. holdfairctl rank-fair-holds --scenario NAME must write /app/work/reconcile-log.json and advance reconcile_pass in /app/state/reconcile-pass.json. holdfairctl write-assignment-atlas --scenario NAME must emit /app/output/hold-assignment-atlas.json only when reconcile_pass is greater than zero.

Suspended patrons must not receive new hold assignments on the reconcile calendar date. Copy routing must honor pickup_branch_id before accepting interbranch transfers allowed by branch policy. Priority class rank uses lower numeric rank as higher priority; ties break by hold_date ascending then patron_id ascending. Environment overrides TB3_FIXTURE_DIR and TB3_RECONCILE_DATE may redirect fixture roots and replace the reconcile calendar date. Bundled scenarios live under /app/fixtures. Do not edit /app/docs/ or /app/fixtures/.
