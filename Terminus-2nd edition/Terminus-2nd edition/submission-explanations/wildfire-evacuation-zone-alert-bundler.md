# Submission explanations - wildfire-evacuation-zone-alert-bundler

**Task folder:** tasks/wildfire-evacuation-zone-alert-bundler/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-08T22:57:08Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is a scientific-computing geospatial metrology closure: county hazard operators publish deterministic wildfire evacuation alert bundles from fire perimeter polygons, evacuation zone footprints, shelter quotas, and road closures. I rated it hard because the numerical behavior is split across scientific-computing-workflow.md, alert-bundle-schema.md, coordinate-geometry-contract.md and kernels like m01_geom.rs / m02_bind.rs. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are seal must read the on-disk weave ledger only, not re-derive everything from raw inputs, and digests have to stay in sync across weave then seal. With about 22 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (m01_geom.rs, m03_slot.rs, m04_journal.rs, m05_prec.rs) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. A second run on unchanged inputs should stay idempotent. Export must respect the replay counter rules.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (22 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
