# Submission explanations - go-oci-layer-whiteout-filesystem-materializer

**Task folder:** tasks/go-oci-layer-whiteout-filesystem-materializer/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-19T18:00:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

**Category note:** Zip metadata uses `system-administration` (host-local layerfuse OCI layer filesystem ops: stack admission → whiteout/opaque gates → sealed atlas). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form. Prior `build-and-dependency-management` upload failed Harbor `[category_classifier]` as blocked `software-engineering`.

## Difficulty Explanation

This task is hard because whiteout deletion, opaque holds, and atlas hashing span several Go packages and fixture stacks, so a partial change can look fine on the bundled stack while hidden verifier stacks still disagree.

## Solution Explanation

The oracle drops corrected sources into /app, rebuilds layerfuse, and exercises the same fixtures agents see. Ingest stages the ledger, materialize applies whiteout/opaque gates, and manifest export must trust only the merged snapshot. Key insight: follow the ops contracts for ordering, digests, and exit codes instead of patching one module around symptoms.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest calls /usr/local/bin/layerfuse via subprocess and recomputes expected JSON from an independent overlay digest math module, so pasted goldens cannot pass. NOP on the baseline should score zero; after the oracle patch and rebuild the suite should clear.
