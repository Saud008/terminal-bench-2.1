# Scientific computing workflow — cement kiln energy balance calibration

This task is a **scientific-computing** industrial metrology workflow. Cement plant operators reconcile heterogeneous pyrometer assays, alternative-fuel batch receipts, clinker tonnage windows, and shell heat-loss budgets into a numerically closed heat balance ledger with sealed staging artifacts. The agent extends thermodynamic unit normalization, probe calibration, fuel-batch lineage binding, linear gap interpolation, and residual scoring on the working baseline under /app so ledger export matches independent reference simulation.

## Numerical scope

| Stage | Closure invariant | Reference |
|-------|-------------------|-----------|
| Therm unit normalize | Kelvin telemetry to Celsius before calibration; kcal fuel CV to MJ | `/app/docs/therm-unit-contract.md` |
| Probe calibration | Offset-corrected Celsius probes before grid fill | `/app/docs/therm-unit-contract.md` |
| Fuel lineage | Inclusive start_ts/end_ts batch windows onto probe timelines | `/app/docs/fuel-batch-lineage.md` |
| Gap interpolation | Linear fill on fixed probe grid (not forward-fill) | `/app/docs/probe-gap-interpolation.md` |
| Residual scoring | energy_in − clinker energy − heat_loss | `/app/docs/heat-balance-residual.md` |
| Ledger digests | Deterministic lineage_digest and audit_digest over sealed rows | `/app/docs/heat-ledger-fields.md` |

## Five-stage calibration pipeline

Stage 1 (`load-probes`) admits kiln-run telemetry into the tele-buffer. Stage 2 (`bind-fuel`) maps fuel batches onto probe timelines. Stage 3 (`interpolate-probes`) materializes the calibrated probe grid. Stage 4 (`score-balance`) persists residual scratch. Stage 5 (`publish-ledger`) reads on-disk staging only and emits heat balance ledger JSON under `/app/output/`. Stage order is fixed: unit normalization and calibration before interpolation, and residual scoring before ledger publish so export digests use calibrated megajoules.

## Operator surface

`kilnbal` is invocable for stages `load-probes`, `bind-fuel`, `interpolate-probes`, `score-balance`, and `publish-ledger`. The installed binary lives at `/app/bin/kilnbal`. Staging buffers follow `/app/docs/tele-buffer-schema.md` and `/app/docs/fuel-buffer-schema.md`. Workspace staging must be in a clean known state before cross-run verifier cases; `/app/scripts/reset-workspace.sh` establishes that invariant. The `grade_decoy` module is outside the calibration hot path.

## Deliverables

- Tele-buffer and fuel-buffer staging under the paths in the buffer schema docs
- Probe-grid JSON after interpolate-probes
- Heat balance ledger JSON under `/app/output/` with `-heat-balance-ledger.json` suffix
- Deterministic digests matching independent reference math in pytest

## Tolerance and verification

Pytest recomputes unit conversion, calibration offsets, inclusive lineage windows, linear interpolation, residual scoring, and digests with independent reference helpers. Hidden procedural fixtures under `/opt/verifier-fixtures/kilnbal` exercise calibration-table and fixture-root overlays not covered by bundled fixtures alone.
