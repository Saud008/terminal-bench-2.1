# Scientific computing workflow — seismic phase-window calibration

This workspace is a scientific-computing seismic metrology laboratory workflow. Network operators reconcile heterogeneous SeedLink SLWS waveform assays into a numerically closed phase-window catalog with sealed staging artifacts. Leap-second chronology calibration, polarity sheet resolution, clip-mask spectral scoring, and phase-window tolerance math must close so catalog export matches independent reference simulation under `/app`.

## Numerical scope

| Stage | Closure invariant | Reference |
|-------|-------------------|-----------|
| CRC validation | Wire checksum before pick chronology parse | `/app/docs/slws-wire-contract.md` |
| Leap adjustment | UTC leap-second table membership shifts pick center times | `/app/docs/leap-calendar.md` |
| Polarity calibration | Station sheet overrides body hint for effective polarity | `/app/docs/phase-window-contract.md` |
| Phase windows | Pre/post microsecond bounds with unit-consistent period_us | `/app/docs/phase-window-contract.md` |
| Clip fraction | LSB-first spectral clip mask within window tolerance | `/app/docs/phase-window-contract.md` |
| Staging digest | FNV-style numeric closure over sample_idx-sorted picks | `/app/docs/phase-staging.md` |

## Two-stage calibration pipeline

Stage 1 persists pick rows and metadata in `/app/state/phase-staging/<stem>.json`. Stage 2 reads staged picks only (never re-parses SLWS for pick rows) and emits phase-window catalog JSON. Stage order is fixed: polarity sheet resolution and leap chronology calibration before digest closure so export windows use calibrated center times.

`seedcat` operator commands for decode, ingest, and catalog export are in `/app/docs/assay-operator-commands.md`. Staging field schemas and digest closure are in `/app/docs/phase-staging.md`. The decoy module at `/app/crates/slcore/src/decoy/legacy_wrap.rs` is outside the calibration hot path; `merge.rs` is not authoritative for export chronology.

## Deliverables

- Phase-window catalog JSON at the caller `--output` path
- Staging snapshot under `/app/state/phase-staging/<stem>.json`
- Deterministic digest and window bounds matching independent reference math

## Tolerance and verification

Independent reference helpers recompute leap adjustments, polarity labels, clip fractions, staging digests, and window bounds. Hidden procedural fixtures under `/opt/verifier-fixtures/` and alternate assay kernels under `/opt/verifier-broken-slcore/` exercise coupling not covered by bundled fixtures alone.
