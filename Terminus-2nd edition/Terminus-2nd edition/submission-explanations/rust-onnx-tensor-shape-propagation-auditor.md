# Submission explanations - rust-onnx-tensor-shape-propagation-auditor

**Task folder:** tasks/rust-onnx-tensor-shape-propagation-auditor/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-06T12:00:32Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about # Tensor graph constraint laboratory I rated it hard because the behavior is split across broadcast_rules.md, diagnostic_contract.md, dynamic_dim_symbols.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and extra probe directories exercise paths the default bundle never hits. With about 22 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (onnx_audit_export.rs, onnx_broadcast_rules.rs, onnx_dim_symbol.rs, onnx_init_bind.rs) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Hidden fixture paths must work without special-casing only the bundled data root.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (22 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
