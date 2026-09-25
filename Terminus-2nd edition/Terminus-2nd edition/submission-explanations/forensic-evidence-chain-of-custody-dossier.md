# Submission explanations - forensic-evidence-chain-of-custody-dossier

**Task folder:** tasks/forensic-evidence-chain-of-custody-dossier/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-10T09:42:13Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about regional forensic labs must publish an offline chain-of-custody dossier that reconciles custody transfers, seal integrity checks, lab intake submissions, approved storage sites, and court. I rated it hard because the behavior is split across case-bundle-catalog.md, chronological-invariant-rules.md, custody-transfer-log-format.md and lib.rs. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and there is at least one decoy source file that looks like the fix target but is not on the hot path. With about 29 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (mod_a.rs, mod_b.rs, mod_c.rs, mod_d.rs) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Re-running on unchanged inputs should produce the same artifacts.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (29 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
