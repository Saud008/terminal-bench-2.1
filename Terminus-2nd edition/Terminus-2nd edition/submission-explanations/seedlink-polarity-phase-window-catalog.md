# Submission explanations - seedlink-polarity-phase-window-catalog

**Task folder:** tasks/seedlink-polarity-phase-window-catalog/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-28T18:30:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `scientific-computing` for SeedLink phase-window metrology laboratory closure (xanes-style short prompt). Choose **Scientific Computing** on the platform form. Do not set `software-engineering` or `debugging` on the form. Prior static check failed the project block list when zip used `debugging`; this restructure restores the scientific-computing laboratory-closure framing rather than a blocked-category label. Keep the short laboratory closure prompt; do not re-add classifier-steering negations (“not a Rust CLI rebuild…”).

## Difficulty Explanation

Previously measured hard, partly from a doc/verifier contradiction on `peak_amplitude` / polarity label (agents often 26–30/31). That section now matches the reference. **Re-run difficulty eval** after this upload; if pass rate rises above the hard bar, add genuine difficulty rather than hidden peak/polarity semantics. Remaining hardness: multi-module leap, polarity, digest, clip, and export-from-staging coupling.

## Solution Explanation

The oracle installs corrected slcore assay kernels, rebuilds seedcat with cargo release, and runs the same subprocess CLI path agents use. The main insight is stage ordering: chronology and polarity calibration must complete before digest closure, and export must read staged pick rows from disk. Decoy modules stay off the export hot path. A second export after staging edits must reflect on-disk bytes, not a fresh parse of the source snippet.

## Verification Explanation

test.sh rebuilds seedcat before pytest. Functional tests invoke `/usr/local/bin/seedcat` via subprocess and compare catalog JSON and staging snapshots to independent reference math in `reference_phase_windows.py`. Hidden fixtures under `/opt/verifier-fixtures/` exercise coupling beyond bundled SLWS files. Alternate-kernel traps swap one broken baseline from `/opt/verifier-broken-slcore/` into the agent tree, rebuild, assert the matching functional check fails, then restore — no golden solution copies under `tests/`. Pack zip with non-`.sh` mode `0644` to avoid EXE002.
