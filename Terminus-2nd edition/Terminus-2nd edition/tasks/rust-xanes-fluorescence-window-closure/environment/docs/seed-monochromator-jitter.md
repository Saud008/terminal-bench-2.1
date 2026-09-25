# Seed monochromator jitter

When `--seed` is set, apply a deterministic monochromator energy nudge derived from that seed before baseline fitting and integration. Only top-level fluorescence windows participate in selecting the nudged point. After the nudge, re-sort the absorption points by ascending energy.
