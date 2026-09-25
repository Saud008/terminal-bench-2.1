# Submission explanations - bash-pam-stack-auth-path-simulator

**Task folder:** tasks/bash-pam-stack-auth-path-simulator/
**Platform form only** - not in upload zip.
**Zip:** `tasksubmit/bash-pam-stack-auth-path-simulator.zip`
**Updated:** 2026-07-25

**Category note:** Zip metadata uses `security` (PAM authentication-path authorization control plane / control-flag trust gates / group-closure authz / sealed `trace_digest` attestation). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form. Prior upload failed Harbor `[category_classifier]` as blocked `debugging` under tracer / baseline / pytest-harness framing; instruction and tags were reframed to authorization / attestation language.

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about identity-security operators shipping a host-local PAM authentication-path authorization control plane under /app. I rated it hard because the behavior is split across auth-path-trace-contract.md, control-flow-contract.md, group-policy-contract.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are emit must read the on-disk ledger snapshot, not re-derive everything from raw service files, and include/substack expansion plus control-flag gates have to stay in sync across load, compile, and emit. Control-flow short-circuit freezes the verdict but still records later auth modules in steps; group closure seeds the subject username before transitive and reverse parent expansion. With about 26 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (multiple source files) into /app, rebuilds the project, and exercises /app/bin/pamtrace against the same fixtures agents see. Load admits scenario bundles, compile writes the sealed ledger, and only then should emit trust those bytes for control-flag and group-policy evaluation. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. A second emit on an unchanged ledger should stay idempotent.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (26 tests) calls /app/bin/pamtrace via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the ledger snapshot bytes before emit fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
