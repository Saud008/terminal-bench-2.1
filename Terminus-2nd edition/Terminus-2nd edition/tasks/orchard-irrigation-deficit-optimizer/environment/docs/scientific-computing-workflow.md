# Scientific computing workflow — orchard irrigation deficit calibration

This task is a **scientific-computing** agronomy metrology workflow. Orchard cooperative operators reconcile heterogeneous soil-moisture probe assays, crop-stage curves, and evapotranspiration forecasts into a numerically closed irrigation deficit plan with sealed ledger artifacts. The agent extends probe calibration, root-zone depth conversion, Kc lookup, probe blending, ET deficit scoring, quota carryover, and pump capacity math on the working baseline under /app so plan export matches independent reference simulation.

## Numerical scope

| Stage | Closure invariant | Reference |
|-------|-------------------|-----------|
| Probe calibration | Offset-corrected volumetric water content before depth conversion | `/app/docs/probe-calibration-contract.md` |
| Root-zone depth | Volumetric fraction to millimeters over root-zone depth | `/app/docs/root-zone-depth-contract.md` |
| Crop Kc lookup | Stage-index crop coefficient for ET demand | `/app/docs/crop-stage-kc-curve.md` |
| Probe blend | Area-weighted field moisture (not arithmetic mean) | `/app/docs/probe-blend-contract.md` |
| Deficit scoring | ET demand and moisture gap millimeters per window | `/app/docs/deficit-scoring-contract.md` |
| Quota carryover | Unused district cubic meters roll forward across windows | `/app/docs/quota-window-carryover.md` |
| Pump ceiling | Liters-per-slot capacity caps total assignment volume | `/app/docs/pump-capacity-contract.md` |
| Ledger digest | Deterministic closure over calibrated field/window rows | `/app/docs/moisture-ledger-schema.md` |
| Plan digest | Deterministic closure over sorted assignments and quota rows | `/app/docs/irrigation-plan-schema.md` |

## Three-stage calibration pipeline

Stage 1 (`load-pack`) admits an orchard field pack and binds it to a run id. Stage 2 (`build-ledger`) materializes calibrated moisture rows and ET demand at `/app/state/moisture-ledger.json`. Stage 3 (`publish-plan`) reads the on-disk moisture ledger only and emits irrigation plan JSON. Stage order is fixed: probe calibration and depth conversion before deficit scoring, and ledger digest before plan publish so export assignments use calibrated millimeters.

## Deliverables

- Moisture ledger JSON at `/app/state/moisture-ledger.json`
- Irrigation plan JSON at the caller `--output` path
- Deterministic digests and deficit assignments matching independent reference math in pytest

## Tolerance and verification

Pytest recomputes probe offsets, depth conversion, Kc lookup, blend weights, ET deficits, quota carryover, pump caps, and digests with independent reference helpers. Hidden procedural fixtures under `/opt/verifier-fixtures/irrctl/` exercise alias and crop-stage coupling not covered by bundled fixtures alone.
