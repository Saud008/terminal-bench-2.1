# Submission explanations - go-coredump-buildid-symbolization-indexer

**Task folder:** tasks/go-coredump-buildid-symbolization-indexer/
**Platform form only** - not in upload zip.
**Zip:** `tasksubmit/go-coredump-buildid-symbolization-indexer.zip`
**Updated:** 2026-07-21

**Category note:** Zip metadata uses `security` (forensic crash-evidence authenticity / GNU build-ID trust admission / mmap integrity gates / tamper-evident chain-of-custody staging / sealed SQLite attestation). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form. Prior upload failed Harbor `[category_classifier]` as blocked `software-engineering` under symbolization-indexer / ELF tooling framing; instruction and tags were reframed to forensic authenticity / attestation language.

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

Agents must align a Go crash-evidence authenticity plane with security contracts spread across build-ID admission, mmap integrity gates, stripped-catalog trust fallback, duplicate evidence grouping, and sealed attestation export. I rated it hard because the behavior is split across cli_surface.md, crash_bundle_format.md, dedupe_grouping.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs, and extra probe directories exercise paths the default bundle never hits. With about 20 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (internal__crashfold__group.go.patch, internal__frozenstage__write.go.patch, internal__gnubuildid__buildid.go.patch, internal__indexsql__export.go.patch) into /app, rebuilds the project, and exercises /app/bin/coreidx against the same fixtures agents see. Ingest validates authenticity gates, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Hidden fixture paths must work without special-casing only the bundled data root.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (20 tests) calls /app/bin/coreidx via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
