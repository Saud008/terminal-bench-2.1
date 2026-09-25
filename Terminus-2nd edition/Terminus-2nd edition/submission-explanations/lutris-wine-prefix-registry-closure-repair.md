# Submission explanations — lutris-wine-prefix-registry-closure-repair

**Task folder:** tasks/lutris-wine-prefix-registry-closure-repair/
**Platform form only** — not in upload zip.

> Edit in your own words before pasting on the platform form.

## Difficulty Explanation

This task is medium because the agent must align four Bash libraries so the lutris-resolve CLI produces contract-correct JSON across nine registry fixtures, not fix a single obvious function. Duplicate-slug merge rules, transitive requires closure with cycle detection, runner inheritance along dependency-first order, prefix symlink canonicalization, and numeric DXVK semver pins are defined across /app/docs/resolve-contract.md, /app/docs/registry-format.md, and /app/docs/resolve-output-schema.md. A partial fix in registry.sh alone still fails transitive-runner or duplicate-merge cases because closure, prefix, and semver layers interact. Exit-code mapping also splits recoverable missing-runner or DXVK failures (exit 1) from unmergeable duplicates and requires cycles (exit 2), which agents often invert when patching one module at a time.

## Solution Explanation

The oracle replaces the four broken libraries under /app/lib/ with golden implementations: registry.sh merges duplicate slugs with unioned requires, conflict checks on runners and provides, and sorted output; closure.sh walks the full transitive graph, detects cycles, emits dependency-first topological order, inherits the last non-empty runner in that order, and picks dxvk_version from the first provider in closure order; prefix.sh resolves relative paths through the full physical symlink chain; semver.sh compares DXVK pins with numeric component ordering rather than ASCII. After install, reset-state.sh restores fixtures and the oracle smoke-runs lutris-resolve on a catalog fixture. The key insight is that runner, prefix, and semver results all depend on the merged registry and correctly ordered closure, so all four modules must agree before any fixture passes.

## Verification Explanation

Pytest drives /app/bin/lutris-resolve via subprocess after reset-state.sh, comparing stdout exit codes and written JSON against an independent reference_resolve.py implementation that re-implements the documented contract. Nine catalog fixtures are parametrized for full JSON equality, and dedicated tests assert deep-chain max_depth, empty closure on cycles, duplicate-merge warnings, missing-slug and missing-runner errors, and conflicting-duplicate exit 2. A seeded registry case recomputes expected output from a verifier seed to block hard-coded answers, and three anti-cheat tests swap only one golden library at a time to prove single-file patches cannot pass the suite. Agents may not edit docs, fixtures, prefixes, config, or tests; only /app/lib/*.sh changes are in scope.
