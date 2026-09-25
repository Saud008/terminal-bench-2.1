# Submission explanations - rust-fido2-attestation-chain-policy-evaluator

**Task folder:** tasks/rust-fido2-attestation-chain-policy-evaluator/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-09T10:07:16Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about enterprise identity teams need an offline FIDO2 and WebAuthn attestation chain policy evaluator that reads registration transcript bundles and publishes trust decisions under enterprise. I rated it hard because the behavior is split across aaguid-metadata-registry.md, bundle-catalog.md, cbor-attestation-layout.md and lib.rs. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are there is at least one decoy source file that looks like the fix target but is not on the hot path. With about 30 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (cache_batch.rs, crypto_authdata.rs, policy_uv.rs, registry_aaguid.rs) into /app, rebuilds the project, and exercises /app/bin/fido2eval against the same fixtures agents see. The fix keeps parsing, core logic, and export aligned with the schemas named in the instruction. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Re-running on unchanged inputs should produce the same artifacts.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (30 tests) calls /app/bin/fido2eval via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Tests mutate paths and inputs enough that hard-coded outputs fail even if one fixture passes. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
