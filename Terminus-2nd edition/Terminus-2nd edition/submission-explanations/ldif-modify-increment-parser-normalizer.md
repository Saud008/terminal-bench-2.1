# Submission explanations — ldif-modify-increment-parser-normalizer

**Task folder:** tasks/ldif-modify-increment-parser-normalizer/
**Platform form only** — not in upload zip.

## Difficulty Explanation

Agents must repair LDIF parsing and apply semantics without a step-by-step fix list. Folding, base64, modify operation order, delete granularity, DN replacement, and case normalization interact across parser.rs and apply.rs. The public API doc names each module boundary, so a patch that fixes one helper while leaving file-order modify sorting or broken unfolding still fails isolated module checks.

## Solution Explanation

The oracle installs corrected parser.rs and apply.rs from solution/oracle, then rebuilds ldif-apply. The key insight is keeping parser token handling separate from apply semantics such as file-order modify ops and add replacing an existing DN. Value-specific deletes and lowercase attribute export must match the JSON and audit contracts.

## Verification Explanation

test.sh runs Rust module contract tests against the documented public API, rebuilds ldif-apply, then pytest against the CLI. Expected JSON comes from reference_apply.py over the same fixtures. Partial-fix cases substitute broken parser.rs or apply.rs alone so one correct module cannot hide a bug in another boundary named in ldif-core-public-api.md.
