# Submission explanations — bash-kernel-config-fragment-merge-attestor

**Task folder:** tasks/bash-kernel-config-fragment-merge-attestor/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must wire a multi-stage Bash pipeline where defconfig and lexicographically ordered fragments merge with last-wins precedence, then a fixed-point dependency closure applies requires, implies, and selects rules before policy scanning. Partial fixes pass bundled cases but fail when export re-reads live files instead of the staged after_deps snapshot, when fragment order is reversed, or when hidden overlay bundles need selects to promote CRC32. Policy traps combine forbidden modular symbols with required-n constraints so one-layer patches leave violations or wrong symbol values.

## Solution Explanation

The oracle repairs fragment ordering to ascending basename sort, merges defconfig first then fragments with later overrides winning, extends dependency closure to propagate implies and selects, treats forbidden_if_set as both y and m, and rewrites emit-manifest to read after_deps and policy_violations directly from kcfg-stage.json. Stage and manifest digests use explicit jq field maps compatible with Debian bookworm jq. CRLF normalization runs on all shell modules before pytest.

## Verification Explanation

Pytest drives kcfgattest through subprocess after rebuild-kcfgattest.sh, compares symbol maps to an independent Python contract in kcfg_contract_math.py, checks staging fields and digests, and uses overlay copies under /opt/verifier-fixtures/kcfg for hidden TB3 imply traps. Tests assert fragment override outcomes, policy violation codes, digest stability across reset-state rebuilds, and that export tracks staged closure rather than a fresh merge from fixtures.
