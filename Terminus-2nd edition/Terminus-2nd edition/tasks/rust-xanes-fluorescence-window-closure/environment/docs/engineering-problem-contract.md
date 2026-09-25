# Engineering problem contract

This scientific-computing laboratory calibration seals nested fluorescence energy windows onto a measured mu(E) absorption spectrum. `xanesctl close` loads one trace JSON and one windows JSON, applies optional seeded monochromator jitter when `--seed` is set, fits a pre-edge baseline, integrates each fluorescence window after baseline subtraction, orders channels by spectroscopic rank, and writes the export described in `closure-schema.md`.

Related spectroscopy contracts: `scientific-computing-workflow.md`, `trace-schema.md`, `window-schema.md`, `victoreen-baseline.md`, `edge-ordinal-table.md`, `window-integral.md`, `seed-monochromator-jitter.md`, `scope-stack.md`, `fixture-catalog.md`.
