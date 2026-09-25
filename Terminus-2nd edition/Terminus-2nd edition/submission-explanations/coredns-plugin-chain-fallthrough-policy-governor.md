# Submission explanations - coredns-plugin-chain-fallthrough-policy-governor

**Task folder:** tasks/coredns-plugin-chain-fallthrough-policy-governor/
**Platform form only** - not in upload zip.
**Updated:** 2026-07-06T18:42:06Z

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about edge DNS facilities rely on each operator to deliver authoritative answers from CoreDNS-style plugin chains. I rated it hard because the behavior is split across corefile-format.md, fixture-catalog.md, README.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are there is at least one decoy source file that looks like the fix target but is not on the hot path. With about 19 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (chain_block_builder.go, chain_sequence_runner.go, fallthrough_eligibility.go, plugin_cache_rcode_key.go) into /app, rebuilds the project, and exercises /app/bin tool against the same fixtures agents see. The fix keeps parsing, core logic, and export aligned with the schemas named in the instruction. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. Re-running on unchanged inputs should produce the same artifacts.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (19 tests) calls /app/bin tool via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Tests mutate paths and inputs enough that hard-coded outputs fail even if one fixture passes. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
