# Submission explanations - rust-avro-schema-evolution-compatibility-ledger

**Task folder:** tasks/rust-avro-schema-evolution-compatibility-ledger/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-05T10:10:16Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about # Avro schema evolution compatibility ledger I rated it hard because the behavior is split across avro_compatibility_overview.md, default_and_union_rules.md, logical_types_and_fingerprint.md and avsc_parse.rs, canon_fp.rs, decoy_metrics.rs, def_promo.rs. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and extra probe directories exercise paths the default bundle never hits. With about 26 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (branch_set.patch, canonical_fp.patch, fqdn_alias.patch, ledger_ingest.patch) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Hidden fixture paths must work without special-casing only the bundled data root.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (26 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
