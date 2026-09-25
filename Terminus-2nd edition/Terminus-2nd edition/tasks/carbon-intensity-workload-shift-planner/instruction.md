Carbon-shift playfield intensity playtest

Build the carbon-shift playfield intensity playtest, an offline grid-window tactics playtest planner for intensity-window scheduling and sealed atlas win-condition export on the working baseline under `/app`. The planner loads scenario playfield packs, applies seeded intensity-window scoring, audits residency allow-list traps and deadline feasibility fences, counts quota-carryover barriers, and seals `publish` playtest atlas exports when the shift-schedule win condition is met. This is a games carbon-shift playfield playtest and sealed-atlas win-condition workflow: keep window normalization, quota carryover barriers, residency refusal, deadline feasibility, intensity-window scoring, fingerprint-bound playfield staging, and sealed atlas exports aligned. It is not a generic Rust CLI engineering, cargo toolchain rebuild, debugging, software-engineering service repair, security admission, data-processing pipeline, or CI tooling exercise.

shift-pl is available at `/app/bin/shift-pl`. Subcommands and flags are cataloged under `/app/docs/`:

```text
shift-pl latch --scenario NAME --run-id ID
shift-pl curate --run-id ID
shift-pl publish --run-id ID --output PATH
```

Playfield contracts under `/app/docs/` define the enforceable win-condition rules:

- `/app/docs/window-normalization-contract.md` — window normalization for playfield epochs
- `/app/docs/quota-carryover-contract.md` — quota carryover barriers
- `/app/docs/residency-policy.md` — residency allow-list refusal traps
- `/app/docs/deadline-feasibility.md` — deadline feasibility fences
- `/app/docs/schedule-scoring.md` — intensity-window scoring
- `/app/docs/infeasible-job-reporting.md` — blocked_jobs reason codes
- `/app/docs/harmonized-ledger-schema.md` — fingerprint-bound playfield staging fields and harmonized_digest
- `/app/docs/shift-schedule-atlas-schema.md` — sealed atlas field order and plan_digest binding
- `/app/docs/scenario-catalog.md` — bundled playfield pack inventory

`latch` admits a scenario pack from the active playfield root and binds it to the run id under `/app/state`.

`curate` materializes the fingerprint-bound playfield staging ledger at `/app/state/shift-harmonized.json` for that run, including region alias map, intensity fingerprint, and `harmonized_digest` per `/app/docs/harmonized-ledger-schema.md`. Curate refuses when intensity or quota integrity gates fail.

`publish` reads the playfield staging ledger only and writes sorted assignment rows, per-window `quota_ledger`, `blocked_jobs` with reason codes, summary counters, and `plan_digest` to the caller-provided path under `/app/output/`. Field order and digest binding follow `/app/docs/shift-schedule-atlas-schema.md`. Publish refuses when the ledger digest is missing or drifted.

Bundled playfield packs live under `/app/fixtures/scenarios`. Hidden verifier packs may mount at `/opt/verifier-fixtures/shift-pl`. Alternate pack roots honor `SHIFT_SCENARIO_ROOT`. Run `/app/scripts/reset-state.sh` before cross-run playtest cases. The lex_rank decoy helper stays outside the latch, curate, and publish playtest hot path. Do not modify `/app/docs/` or `/app/fixtures/`. Offline only.
