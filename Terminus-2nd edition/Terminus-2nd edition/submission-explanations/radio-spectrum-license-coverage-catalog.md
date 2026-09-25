# Submission explanations - radio-spectrum-license-coverage-catalog

**Task folder:** tasks/radio-spectrum-license-coverage-catalog/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-28T03:40:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about regulatory coordinators publish an analytical RF license atlas from grant bundles under /opt/rflicat-bundles/bundles/. I rated it hard because the behavior is split across atlas-row-schema.md, bundle-catalog.md, coverage-generation-schema.md and catalog_schema.rs, lib.rs, rflicat_main.rs. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and replay counters and commit files have to stay in sync across two CLI runs. With about 28 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The shipped environment must compile (Docker runs `cargo build --release --locked`), so call sites use `geo_fence` / `tenure_gate` rather than leftover `territory` / `validity` names. The oracle installs corrected sources from `solution/files/` (WAL load_generation, inclusive bbox edges, highest-priority coupling, carveout polarity, renewal `>=`, touching MHz overlap, summary counters, `atl-` atlas_seq_id, holder/band/site sort), rebuilds `/app/bin/rflicat`, and resets state. Prepare writes the WAL frame and coverage row; render must trust that staging state for sealed atlas export.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (28 tests) calls /app/bin/rflicat via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
