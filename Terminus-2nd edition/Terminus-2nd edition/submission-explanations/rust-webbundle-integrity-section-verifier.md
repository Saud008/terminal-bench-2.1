# Submission explanations - rust-webbundle-integrity-section-verifier

**Task folder:** tasks/rust-webbundle-integrity-section-verifier/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-06T12:10:23Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about # Signed-exchange bundle attestation lab I rated it hard because the behavior is split across evidence_report.md, scope_and_integrity.md, url_canonicalization.md and lib.rs, wbleguard_main.rs. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and extra probe directories exercise paths the default bundle never hits. With about 24 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (sb_attestation_emit.rs, sb_attestation_ledger.rs, sb_hdr_fold.rs, sb_ihsh_digest.rs) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Hidden fixture paths must work without special-casing only the bundled data root.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (24 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
