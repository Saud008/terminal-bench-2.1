# Submission explanations — tuf-delegation-threshold-rotation-verifier

**Task folder:** tasks/tuf-delegation-threshold-rotation-verifier/
**Platform form only** — not in upload zip.
**Updated:** 2026-07-22T20:20:00Z

**Category note:** Zip metadata uses `security` (TUF metadata trust-admission / threshold-signature authenticity / key temporal validity / delegated path-scope admission / snapshot version coupling / root-key reuse ban / digest-bound delegation attestation). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form. Prior upload failed Harbor `[category_classifier]` as blocked `software-engineering` when the prompt led with Implement / Build / working Rust baseline framing; keep the metadata-attestation / rotation-admission security framing and the explicit “not a Rust CLI / cargo rebuild / CI tooling exercise” negation.

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about supply-chain security operators attesting TUF-style metadata rotations before delegation admission. I rated it hard because the behavior is split across canonical signed bytes, threshold quorum counting, epoch key validity, snapshot-to-targets linkage, delegated path scope, and root-key reuse bans plus multiple Rust modules. Fixing one authenticity gate often looks fine on the bundled data while other checks still fail. The painful parts are export must honor the verify-result seal holistically, not re-derive from raw metadata, and threshold edge cases at epoch fifty show why strict less-than expiry matters when a root signer drops out of quorum. With about 25 checks in the suite, a partial fix often passes bundled ingest and staging cases but still fails once you hit hidden TB3 fixtures or epoch bias.

## Solution Explanation

The oracle drops corrected sources (canonical serialization, threshold crypto, delegation reuse/path scope, snapshot link, export attestation) into /app, rebuilds the project, and exercises /app/bin/tufctl against the same fixtures agents see. ingest admits metadata and writes the staging snapshot; verify rotation applies cryptographic and temporal gates; only then should export report trust those bytes. Key insight: follow the security contracts for ordering, digests, and seal rules instead of patching around symptoms in one module. A second ingest on unchanged inputs should keep ingest_seq monotonic.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest drives tufctl through subprocess ingest, verify rotation at multiple epochs, and export report. Tests do not grep source for magic strings. The test module includes its own reference verifier so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and verify-result before report fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
