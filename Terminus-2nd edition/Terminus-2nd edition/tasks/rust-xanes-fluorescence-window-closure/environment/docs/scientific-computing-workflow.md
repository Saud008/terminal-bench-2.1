# Scientific computing workflow

Each laboratory calibration close must:

1. Load one mu(E) absorption trace and one nested fluorescence window tree.
2. Apply optional seeded monochromator energy jitter when `--seed` is set.
3. Fit the pre-edge baseline, integrate each fluorescence window after baseline subtraction, and rank channels by spectroscopic edge ordinal.
4. Emit the sealed closure export described in `closure-schema.md`.

Independent verifier reference math recomputes the same digests without invoking the operator binary. Pytest may clear `/app/output` between cross-run cases.
