Seismic network metrology teams use `seedcat` for scientific-computing SeedLink phase-window laboratory calibration closure on SLWS waveform snippets, station polarity sheets, leap-second chronology tables, and clipped-sample spectral masks. That calibration path is broken: sealed staging snapshots and catalog JSON must match the laboratory contracts under `/app/docs/` (`scientific-computing-workflow.md`, `slws-wire-contract.md`, `leap-calendar.md`, `phase-window-contract.md`, `phase-staging.md`, `assay-operator-commands.md`, and `fixture-catalog.md`).

Bundled SLWS snippets live under `/app/fixtures/slws/`, with scenario intent in `/app/docs/fixture-catalog.md`. Alternate leap and polarity tables honor `TB3_LEAP_ROOT` and `TB3_POLARITY_ROOT`. Hidden waveform fixtures honor verifier overlay roots. Produce a release binary invocable as `seedcat` that satisfies those laboratory contracts.

Do not modify `/app/docs/`, `/app/fixtures/`, or `/tests/`.
