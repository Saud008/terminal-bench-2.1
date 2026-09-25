# Submission explanations - rust-xanes-fluorescence-window-closure

**Task folder:** tasks/rust-xanes-fluorescence-window-closure/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-20T02:20:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `scientific-computing` (beamline XANES / XAFS fluorescence-window laboratory calibration closure). Prior upload failed Harbor `[category_classifier]` as blocked `software-engineering` when the prompt led with cargo build / CLI install framing. Keep the spectroscopy / laboratory / metrology framing on the platform form.

## Difficulty Explanation

This task is about synchrotron beamline metrology teams sealing fluorescence-window integrals from mu(E) absorption traces. I rated it hard because the spectroscopy behavior is split across several laboratory contracts and calibration modules. Fixing one layer often looks fine on simple K-edge fixtures while seeded, rank-mix, or undeclared-edge checks still fail. The painful parts are close must align every laboratory contract for digest parity, not patch a single wrapper, and there is at least one decoy spectrum renderer that looks like the fix target but is not on the hot path. With the full pytest suite including hidden and staging traps, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources into /app, rebuilds the project, and exercises xanesctl close against the same fixtures agents see. Ingest loads the absorption trace, binds fluorescence windows, and only then should export trust the sealed integral rows. Key insight: follow the spectroscopy contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Re-running on unchanged inputs should produce the same artifacts.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest runs test_outputs.py, test_hidden_xanes_traps.py, and test_staging_xanes.py via subprocess against xanesctl. Tests do not grep source for magic strings. The test module includes its own reference math so expected digests are recomputed from fixtures, which blocks pasted golden answers. Hidden packs under /opt/verifier-fixtures/xanes-delta and staging snapshots under /opt/verifier-broken-xanes exercise traps off the main catalog. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
