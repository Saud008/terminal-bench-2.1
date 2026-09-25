Library consortium operators run the host-local holdfairctl hold-queue fairness control plane at /app/bin/holdfairctl. Each offline ops pass mounts a library scenario database, composes the hold-queue rollup, ranks fair holds under suspension and branch-routing gates, then publishes a sealed assignment atlas only from a committed reconcile pass. There is no remote ILS or consortial API. This is a system-administration host-local library hold-queue ops control plane; keep suspension admission, pickup-branch routing, reconcile-pass seals, and sealed atlas export aligned. It is not a generic service repair exercise.

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
