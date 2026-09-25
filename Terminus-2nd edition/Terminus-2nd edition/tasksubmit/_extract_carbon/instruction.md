Grid-ops administrators run the host-local shift-pl carbon-intensity shift-schedule control plane at /app/bin/shift-pl. Each offline ops pass admits a scenario fixture into a run-bound latch, materializes a fingerprint-bound harmonized ledger under intensity fingerprint and quota carryover gates, then publishes a sealed shift-schedule atlas only from that committed ledger. There is no live grid API or remote intensity feed. This is a system-administration host-local carbon intensity shift-schedule ops control plane; keep scenario latch admission, intensity fingerprint gates, quota carryover barriers, residency allow-list refusal, deadline feasibility checks, and sealed atlas export aligned. It is not a Rust CLI rebuild, cargo toolchain exercise, pytest harness, or generic service repair exercise.

Ops contracts under /app/docs/ define the enforceable invariants:

- /app/docs/window-normalization-contract.md — window normalization for fixture epochs
- /app/docs/quota-carryover-contract.md — quota carryover barriers
- /app/docs/residency-policy.md — residency allow-list refusal
- /app/docs/deadline-feasibility.md — deadline feasibility checks
- /app/docs/schedule-scoring.md — schedule scoring under intensity windows
- /app/docs/infeasible-job-reporting.md — blocked_jobs reason codes
- /app/docs/harmonized-ledger-schema.md — fingerprint-bound ledger fields and harmonized_digest
- /app/docs/shift-schedule-atlas-schema.md — sealed atlas field order and plan_digest binding
- /app/docs/scenario-catalog.md — bundled scenario inventory

shift-pl latch --scenario NAME --run-id ID must admit a scenario bundle from the active fixture root and bind it to the run id under /app/state.

shift-pl curate --run-id ID must materialize the fingerprint-bound harmonized ledger at /app/state/shift-harmonized.json for that run, including region alias map, intensity fingerprint, and harmonized_digest per /app/docs/harmonized-ledger-schema.md. Curate must refuse when intensity or quota integrity gates fail.

shift-pl publish --run-id ID --output PATH must read the harmonized ledger only and write sorted assignment rows, per-window quota_ledger, blocked_jobs with reason codes, summary counters, and plan_digest to the caller-provided path under /app/output/. Field order and digest binding follow /app/docs/shift-schedule-atlas-schema.md. Publish must refuse when the ledger digest is missing or drifted.

Install the binary at /app/bin/shift-pl from the host-local ops tree under /app. Bundled fixtures live under /app/fixtures/scenarios. Hidden verifier fixtures may mount at /opt/verifier-fixtures/shift-pl. Alternate scenario roots honor SHIFT_SCENARIO_ROOT. Use /app/scripts/reset-state.sh between cross-run checks. The lex_rank decoy module is not on the latch, curate, or publish hot path and must not influence correct export. Do not edit /app/docs/ or /app/fixtures/.
