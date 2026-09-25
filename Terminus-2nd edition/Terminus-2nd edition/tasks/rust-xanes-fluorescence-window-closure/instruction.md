Synchrotron beamline metrology teams use `xanesctl close` for scientific-computing XANES fluorescence-window laboratory calibration closure on mu(E) absorption traces. That close path is broken: sealed exports must match the spectroscopy contracts under `/app/docs/` (see `engineering-problem-contract.md` and `scientific-computing-workflow.md`).

Bundled absorption traces and fluorescence window packs live under `/app/fixtures/traces/` and `/app/fixtures/windows/`, with scenario intent in `/app/docs/fixture-catalog.md`. Produce a release binary invocable as `xanesctl close` that satisfies those laboratory contracts.

Do not modify `/app/docs/`, `/app/fixtures/`, or `/tests/`.
