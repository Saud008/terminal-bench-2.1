# Submission explanations - substation-switching-order-interlock-checker

**Task folder:** tasks/substation-switching-order-interlock-checker/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-19T14:56:00Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is an offline access-decision admission gate: relayctl must stage tamper-evident yard/LOTO witnesses, enforce LOTO authenticity and interlock deny-overrides, and publish digest-sealed audit attestation with no live SCADA. I rated it hard because the security behavior is split across lockout-tag-policy.md, interlock-constraint-catalog.md, energization-propagation-contract.md and loto_enforce.rs, mux_isolation.rs, diag_emit.rs, energize_propagate.rs. Fixing one authorization layer often looks fine on bundled yards while other policy checks still fail. The painful parts are verify-order must trust the on-disk yard.snapshot and loto.ticket witnesses, not re-derive policy from raw fixtures, and there is at least one decoy source file that looks like the fix target but is not on the hot path. With about 23 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second admit.

## Solution Explanation

The oracle drops corrected sources (diag_emit.rs, loto_enforce.rs, mux_isolation.rs, proc_walk.rs) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and any commit-bind metadata, and only then should export trust those bytes. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Re-running on unchanged inputs should produce the same artifacts.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (23 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot and manifest bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
